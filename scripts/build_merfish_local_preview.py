from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

SOURCE_ID = "human-skin-spatial-census"
DEFAULT_INPUT = Path("data/raw/merfish.integrated_annotated.h5ad")
DEFAULT_OUTPUT = Path("data/reference/human-skin-spatial-census/cells_preview.json")
DEFAULT_LIMIT = 1000
DEFAULT_REGIONS = ("palm", "hand", "elbow")


def _normalise(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pick_column(columns: Iterable[object], candidates: tuple[str, ...]) -> str | None:
    by_lower = {str(column).strip().lower(): str(column) for column in columns}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return None


def _as_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_preview(
    input_path: Path,
    output_path: Path,
    limit: int = DEFAULT_LIMIT,
    regions: Iterable[str] = DEFAULT_REGIONS,
) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(f"AnnData input not found: {input_path}")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    requested_regions = tuple(dict.fromkeys(
        str(region).strip().lower() for region in regions if str(region).strip()
    ))
    if not requested_regions:
        raise ValueError("at least one region is required")

    import scanpy as sc

    adata = sc.read_h5ad(input_path, backed="r")
    try:
        obs = adata.obs
        columns = tuple(obs.columns)
        cell_id_column = _pick_column(columns, ("cellId", "cell_id", "cellid", "CellID", "cell"))
        anatomic_column = _pick_column(columns, ("anatomicSite", "anatomic_site", "anatomicalSite", "anatomical_site", "site"))
        region_column = _pick_column(columns, ("regionName", "region_name", "region", "Region"))
        x_column = _pick_column(columns, ("x", "X", "spatial_x", "spatialX", "center_x", "centroid_x"))
        y_column = _pick_column(columns, ("y", "Y", "spatial_y", "spatialY", "center_y", "centroid_y"))

        spatial = None
        for key in ("spatial", "X_spatial", "X_spatial_coords"):
            if key in adata.obsm:
                spatial = adata.obsm[key]
                break

        cells: list[dict] = []
        counts = {region: 0 for region in requested_regions}
        for index in range(adata.n_obs):
            row = obs.iloc[index]
            anatomic_site = _normalise(row[anatomic_column]) if anatomic_column else None
            region_name = _normalise(row[region_column]) if region_column else None
            searchable = " ".join(filter(None, (anatomic_site, region_name))).lower()
            matched_region = next(
                (region for region in requested_regions if region in searchable),
                None,
            )
            if matched_region is None or counts[matched_region] >= limit:
                continue

            cell_id = _normalise(row[cell_id_column]) if cell_id_column else _normalise(obs.index[index])
            if not cell_id:
                continue

            x = _as_float(row[x_column]) if x_column else None
            y = _as_float(row[y_column]) if y_column else None
            if (x is None or y is None) and spatial is not None:
                try:
                    x = _as_float(spatial[index][0])
                    y = _as_float(spatial[index][1])
                except (IndexError, TypeError):
                    pass
            if x is None or y is None:
                continue

            cells.append({
                "cellId": cell_id,
                "anatomicSite": anatomic_site,
                "regionName": region_name,
                "x": x,
                "y": y,
            })
            counts[matched_region] += 1

            if all(count >= limit for count in counts.values()):
                break
    finally:
        adata.file.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": "1.0.0",
        "sourceId": SOURCE_ID,
        "sourceDataset": "human-skin-spatial-census-merfish",
        "accession": "S-BIAD2376",
        "technology": "MERFISH",
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "input": {
            "path": str(input_path),
            "sizeBytes": input_path.stat().st_size,
            "sha256": _sha256(input_path),
        },
        "extraction": {
            "method": "AnnData obs + spatial coordinates",
            "regions": list(requested_regions),
            "maxCellsPerRegion": limit,
            "selectionOrder": "source observation order",
            "cellIdFallback": "AnnData obs index",
        },
        "countsByRequestedRegion": counts,
        "cells": cells,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize bounded MERFISH cell-coordinate previews without copying the expression matrix."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument(
        "--region",
        action="append",
        dest="regions",
        help="Region/site substring to include; repeat for multiple regions. Defaults to palm, hand and elbow.",
    )
    args = parser.parse_args()

    payload = build_preview(
        args.input,
        args.output,
        args.limit,
        tuple(args.regions) if args.regions else DEFAULT_REGIONS,
    )
    print(json.dumps({
        "status": "ok",
        "sourceId": payload["sourceId"],
        "cells": len(payload["cells"]),
        "countsByRequestedRegion": payload["countsByRequestedRegion"],
        "output": str(args.output),
        "inputSha256": payload["input"]["sha256"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
