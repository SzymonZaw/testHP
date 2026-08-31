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
DEFAULT_OUTPUT = ROOT / "data" / "reference" / "human-skin-spatial-census" / "cells_preview.json"
DEFAULT_LIMIT = 1000
MAX_LIMIT = 1000


def _strings(dataset: h5py.Dataset, indices: np.ndarray | None = None) -> list[str]:
    values = dataset.asstr()[:] if indices is None else dataset.asstr()[indices]
    return [str(value) for value in values]


def _categories(group: h5py.Group) -> list[str]:
    return _strings(group["categories"])


def build_preview(input_path: Path, output_path: Path, anatomic_site: str, limit: int) -> dict:
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
        try:
            category_code = normalized.index(requested_site)
        except ValueError:
            return {
                "sourceFile": str(input_path.relative_to(ROOT)),
                "sourceCellCount": int(obs["_index"].shape[0]),
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
            "sourceFile": str(input_path.relative_to(ROOT)),
            "sourceCellCount": int(obs["_index"].shape[0]),
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize a small local MERFISH preview from a H5AD file."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--anatomic-site", default="forearm")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    payload = build_preview(args.input.resolve(), args.output.resolve(), args.anatomic_site, args.limit)
    write_atomic(payload, args.output.resolve())
    print(
        f"Wrote {payload['returnedCount']} cells for {payload['anatomicSite']!r} "
        f"to {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
