from __future__ import annotations

import argparse
import json
from collections import Counter
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


def read_obs_values(group: h5py.Group, key: str, start: int, stop: int) -> np.ndarray:
    """Read one AnnData obs column, supporting datasets and pandas categorical groups."""
    node = group[key]
    if isinstance(node, h5py.Dataset):
        return np.asarray(node[start:stop])

    if not isinstance(node, h5py.Group):
        raise TypeError(f"Unsupported HDF5 node for obs[{key!r}]: {type(node).__name__}")

    if "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"][start:stop])
        categories = np.asarray(node["categories"][:])
        values = []
        for code in codes:
            idx = int(decode(code))
            values.append(categories[idx] if 0 <= idx < len(categories) else None)
        return np.asarray(values, dtype=object)

    raise TypeError(
        f"Unsupported obs group encoding for {key!r}; expected categorical codes/categories"
    )


def read_obs_value(group: h5py.Group, key: str, index: int):
    """Read a single obs value using the same dataset/categorical rules."""
    values = read_obs_values(group, key, index, index + 1)
    return decode(values[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bounded local preview from the MERFISH H5AD.")
    parser.add_argument("h5ad", type=Path, help="Path to merfish.integrated_annotated.h5ad")
    parser.add_argument("--region", default="palm", help="Case-insensitive substring for anatomic_site or region_name")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--list-regions", action="store_true", help="Print observed anatomic_site/region_name labels and exit")
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

        total = int(obs["cell_id"].shape[0]) if isinstance(obs["cell_id"], h5py.Dataset) else int(obs["cell_barcode"].shape[0])
        matches: list[int] = []
        site_counts: Counter[str] = Counter()
        region_counts: Counter[str] = Counter()
        needle = args.region.strip().lower()
        chunk = 5000
        for start in range(0, total, chunk):
            stop = min(total, start + chunk)
            sites = read_obs_values(obs, "anatomic_site", start, stop)
            regions = read_obs_values(obs, "region_name", start, stop)
            for offset, (site, region) in enumerate(zip(sites, regions)):
                site_text = str(decode(site) or "")
                region_text = str(decode(region) or "")
                site_counts[site_text] += 1
                region_counts[region_text] += 1
                if needle and (needle in site_text.lower() or needle in region_text.lower()):
                    matches.append(start + offset)
                    if len(matches) >= args.limit:
                        break
            if len(matches) >= args.limit:
                break

        if args.list_regions:
            print("Observed anatomic_site labels:")
            for label, count in site_counts.most_common():
                print(f"  {count:>7}  {label}")
            print("Observed region_name labels:")
            for label, count in region_counts.most_common():
                print(f"  {count:>7}  {label}")
            return 0

        if not matches:
            print(f"No cells matched region={args.region!r}.")
            print("Top anatomic_site labels:")
            for label, count in site_counts.most_common(20):
                print(f"  {count:>7}  {label}")
            print("Top region_name labels:")
            for label, count in region_counts.most_common(20):
                print(f"  {count:>7}  {label}")
            raise SystemExit(2)

        rows: list[dict[str, object]] = []
        spatial = obsm["spatial"]
        for index in matches:
            point = np.asarray(spatial[index]).reshape(-1)
            coords = [float(point[0]), float(point[1])] if point.size >= 2 else []
            row = {key: read_obs_value(obs, key, index) for key in REQUIRED_OBS}
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
