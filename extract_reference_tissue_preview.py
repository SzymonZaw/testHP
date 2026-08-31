from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "data" / "raw" / "merfish.integrated_annotated.h5ad"
DEFAULT_OUTPUT = ROOT / "data" / "reference" / "human-skin-spatial-census"
DEFAULT_LIMIT = 1000
MAX_LIMIT = 1000


def _strings(dataset: h5py.Dataset, indices: np.ndarray | None = None) -> list[str]:
    values = dataset.asstr()[:] if indices is None else dataset.asstr()[indices]
    return [str(value) for value in values]


def _categories(group: h5py.Group) -> list[str]:
    return _strings(group["categories"])


def build_preview(input_path: Path, anatomic_site: str, limit: int) -> dict:
    if limit < 1 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    if not input_path.is_file():
        raise FileNotFoundError(f"H5AD not found: {input_path}")

    requested_site = anatomic_site.strip().lower()
    if not requested_site:
        raise ValueError("anatomic_site must not be empty")

    with h5py.File(input_path, "r") as h5:
        obs = h5["obs"]
        obsm = h5["obsm"]
        site_group = obs["anatomic_site"]
        categories = _categories(site_group)
        normalized = [value.strip().lower() for value in categories]
        source_count = int(obs["_index"].shape[0])

        try:
            category_code = normalized.index(requested_site)
        except ValueError:
            return {
                "status": "bounded_local_cell_preview_empty",
                "sourceFile": str(input_path.relative_to(ROOT)),
                "sourceCellCount": source_count,
                "region": requested_site,
                "anatomicSite": requested_site,
                "requestedLimit": limit,
                "returnedCount": 0,
                "cells": [],
                "coordinateScope": "sample_local",
                "registrationStatus": "unregistered_to_hand",
                "transform": None,
                "matrixLoaded": False,
                "dataLoaded": True,
                "note": "No cells matched the requested anatomic_site in the local H5AD.",
            }

        codes = np.asarray(site_group["codes"])
        selected = np.flatnonzero(codes == category_code)[:limit]
        spatial = np.asarray(obsm["spatial"][selected], dtype=np.float64)
        cell_ids = _strings(obs["cell_id"], selected) if "cell_id" in obs else _strings(obs["_index"], selected)

        region_names: list[str | None] = [None] * len(selected)
        if "region_name" in obs:
            region_group = obs["region_name"]
            region_categories = _categories(region_group)
            region_codes = np.asarray(region_group["codes"])[selected]
            region_names = [
                region_categories[int(code)] if int(code) >= 0 else None
                for code in region_codes
            ]

        cells = [
            {
                "cellId": cell_id,
                "anatomicSite": categories[category_code],
                "regionName": region_name,
                "x": float(point[0]),
                "y": float(point[1]),
            }
            for cell_id, region_name, point in zip(cell_ids, region_names, spatial)
        ]

        return {
            "status": "bounded_local_cell_preview",
            "sourceFile": str(input_path.relative_to(ROOT)),
            "sourceCellCount": source_count,
            "region": categories[category_code],
            "anatomicSite": categories[category_code],
            "requestedLimit": limit,
            "returnedCount": len(cells),
            "cells": cells,
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "matrixLoaded": False,
            "dataLoaded": True,
            "note": "Real MERFISH cells materialized from local H5AD. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
        }


def write_atomic(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, separators=(",", ":"))
        tmp.write("\n")
        temporary = Path(tmp.name)
    os.replace(temporary, output_path)


def discover_sites(input_path: Path) -> list[str]:
    with h5py.File(input_path, "r") as h5:
        return _categories(h5["obs"]["anatomic_site"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize small local MERFISH previews from a H5AD file."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--anatomic-site", action="append", dest="anatomic_sites")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    sites = args.anatomic_sites or discover_sites(input_path)

    regions: dict[str, dict] = {}
    for site in sites:
        payload = build_preview(input_path, site, args.limit)
        safe_name = site.strip().lower().replace(" ", "-")
        output_path = output_dir / f"{safe_name}.json"
        write_atomic(payload, output_path)
        regions[site] = {
            "file": output_path.name,
            "cellCount": payload["returnedCount"],
        }
        print(f"Wrote {payload['returnedCount']} cells for {site!r} to {output_path}")

    manifest = {
        "status": "bounded_local_cell_preview_manifest",
        "sourceFile": str(input_path.relative_to(ROOT)),
        "sourceCellCount": build_preview(input_path, sites[0], 1)["sourceCellCount"],
        "limitPerRegion": args.limit,
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "regions": regions,
        "note": "Precomputed local MERFISH previews. No H5AD reads are required by the web request path.",
    }
    write_atomic(manifest, output_dir / "manifest.json")
    print(f"Wrote manifest to {output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
