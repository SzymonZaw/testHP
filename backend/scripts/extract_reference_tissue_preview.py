from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import h5py
import numpy as np

REQUIRED_OBS = ["cell_id", "cell_barcode", "anatomic_site", "region_name", "sample_id"]
DEFAULT_OUTPUT = Path("data/reference/human-skin-spatial-census/palm_cells.json")
DEFAULT_LIMIT = 1000
SEARCH_FIELDS = [
    "anatomic_site",
    "region_name",
    "sample_id",
    "sample_barcode",
    "run_name",
    "run_name.short",
    "run_region",
    "collection_source",
    "collection_type",
    "sample_compartment",
    "component",
]


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
    return decode(read_obs_values(group, key, index, index + 1)[0])


def dataset_length(node: h5py.Dataset | h5py.Group) -> int:
    if isinstance(node, h5py.Dataset):
        return int(node.shape[0])
    if isinstance(node, h5py.Group):
        if "codes" in node:
            return int(node["codes"].shape[0])
        for child in node.values():
            if isinstance(child, h5py.Dataset) and child.ndim:
                return int(child.shape[0])
    raise TypeError(f"Cannot determine AnnData column length for {type(node).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bounded local preview from the MERFISH H5AD.")
    parser.add_argument("h5ad", type=Path, help="Path to merfish.integrated_annotated.h5ad")
    parser.add_argument("--region", default="palm", help="Case-insensitive search term")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--list-regions", action="store_true", help="Print observed anatomic_site/region_name labels and exit")
    parser.add_argument("--list-samples", action="store_true", help="Print sample_id/sample_barcode/run_name with anatomic_site counts and exit")
    parser.add_argument("--search-all-obs", action="store_true", help="Search additional text obs fields for the requested term")
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

        total = dataset_length(obs[REQUIRED_OBS[0]])
        site_counts: Counter[str] = Counter()
        region_counts: Counter[str] = Counter()
        sample_counts: Counter[tuple[str, str, str, str]] = Counter()
        search_fields = [k for k in SEARCH_FIELDS if k in obs]
        if args.search_all_obs:
            search_fields = list(obs.keys())

        needle = args.region.strip().lower()
        matches: list[int] = []
        matched_fields: Counter[str] = Counter()
        chunk = 5000

        for start in range(0, total, chunk):
            stop = min(total, start + chunk)
            sites = read_obs_values(obs, "anatomic_site", start, stop)
            regions = read_obs_values(obs, "region_name", start, stop)

            samples = read_obs_values(obs, "sample_id", start, stop)
            sample_barcodes = read_obs_values(obs, "sample_barcode", start, stop) if "sample_barcode" in obs else np.array([None] * len(sites), dtype=object)
            run_names = read_obs_values(obs, "run_name", start, stop) if "run_name" in obs else np.array([None] * len(sites), dtype=object)

            for offset, (site, region, sample, barcode, run_name) in enumerate(zip(sites, regions, samples, sample_barcodes, run_names)):
                site_text = str(decode(site) or "")
                region_text = str(decode(region) or "")
                sample_text = str(decode(sample) or "")
                barcode_text = str(decode(barcode) or "")
                run_text = str(decode(run_name) or "")
                site_counts[site_text] += 1
                region_counts[region_text] += 1
                sample_counts[(sample_text, barcode_text, run_text, site_text)] += 1

            if needle:
                row_hits: set[int] = set()
                for field in search_fields:
                    values = read_obs_values(obs, field, start, stop)
                    for offset, value in enumerate(values):
                        text = str(decode(value) or "").lower()
                        if needle in text:
                            row_hits.add(start + offset)
                            matched_fields[field] += 1
                for index in sorted(row_hits):
                    matches.append(index)
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

        if args.list_samples:
            print("Observed MERFISH sample mapping:")
            print("count | sample_id | sample_barcode | run_name | anatomic_site")
            for (sample_id, sample_barcode, run_name, site), count in sorted(
                sample_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2], item[0][3])
            ):
                print(f"{count:>7} | {sample_id} | {sample_barcode} | {run_name} | {site}")
            return 0

        if not matches:
            print(f"No cells matched search term={args.region!r}.")
            print("Fields searched:", ", ".join(search_fields))
            print("Match counts by field:")
            for field, count in matched_fields.most_common():
                print(f"  {count:>7}  {field}")
            if not args.search_all_obs:
                print("Tip: rerun with --search-all-obs to search all textual obs fields.")
            raise SystemExit(2)

        rows: list[dict[str, object]] = []
        spatial = obsm["spatial"]
        for index in matches[: args.limit]:
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
        "matchedFields": dict(matched_fields),
        "cells": rows,
        "note": "Locally materialized bounded extract. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} cells to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
