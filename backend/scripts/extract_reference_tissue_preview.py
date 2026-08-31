from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np

REQUIRED_OBS = ["cell_id", "cell_barcode", "anatomic_site", "region_name", "sample_id"]
DEFAULT_OUTPUT = Path("data/reference/human-skin-spatial-census/palm_cells.json")
DEFAULT_LIMIT = 1000


def decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bounded local preview from the MERFISH H5AD.")
    parser.add_argument("h5ad", type=Path, help="Path to merfish.integrated_annotated.h5ad")
    parser.add_argument("--region", default="palm", choices=["palm", "hand"])
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.h5ad.is_file():
        raise SystemExit(f"H5AD not found: {args.h5ad}")
    if not 1 <= args.limit <= 10000:
        raise SystemExit("--limit must be between 1 and 10000")

    with h5py.File(args.h5ad, "r") as handle:
        if "obs" not in handle or "obsm" not in handle:
            raise SystemExit("H5AD is missing AnnData obs/obsm groups")
        obs = handle["obs"]
        obsm = handle["obsm"]
        missing = [key for key in REQUIRED_OBS if key not in obs]
        if missing:
            raise SystemExit(f"Missing required obs fields: {', '.join(missing)}")
        if "spatial" not in obsm:
            raise SystemExit("AnnData obsm/spatial is missing")

        total = int(obs["cell_id"].shape[0])
        matches: list[int] = []
        needle = args.region.lower()
        chunk = 5000
        for start in range(0, total, chunk):
            stop = min(total, start + chunk)
            sites = np.asarray(obs["anatomic_site"][start:stop])
            regions = np.asarray(obs["region_name"][start:stop])
            for offset, (site, region) in enumerate(zip(sites, regions)):
                if needle in str(decode(site)).lower() or needle in str(decode(region)).lower():
                    matches.append(start + offset)
                    if len(matches) >= args.limit:
                        break
            if len(matches) >= args.limit:
                break

        rows: list[dict[str, object]] = []
        spatial = obsm["spatial"]
        for index in matches:
            point = np.asarray(spatial[index]).reshape(-1)
            coords = [float(point[0]), float(point[1])] if point.size >= 2 else []
            row = {key: decode(obs[key][index]) for key in REQUIRED_OBS}
            row["index"] = int(index)
            row["spatial"] = coords
            rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sourceId": "human-skin-spatial-census",
        "sourceFile": args.h5ad.name,
        "region": args.region,
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "transform": None,
        "sourceCellCount": total,
        "returnedCount": len(rows),
        "cells": rows,
        "note": "Locally materialized bounded extract. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} cells to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
