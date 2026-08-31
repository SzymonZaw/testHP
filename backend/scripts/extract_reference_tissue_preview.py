from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import h5py
import numpy as np

REQUIRED_OBS = ["cell_id", "cell_barcode", "anatomic_site", "region_name", "sample_id"]
DEFAULT_OUTPUT = Path("data/reference/human-skin-spatial-census/cells_preview.json")
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
    node = group[key]
    if isinstance(node, h5py.Dataset):
        return np.asarray(node[start:stop])
    if isinstance(node, h5py.Group) and "codes" in node and "categories" in node:
        codes = np.asarray(node["codes"][start:stop])
        categories = np.asarray(node["categories"][:])
        return np.asarray([
            categories[int(decode(code))] if 0 <= int(decode(code)) < len(categories) else None
            for code in codes
        ], dtype=object)
    raise TypeError(f"Unsupported AnnData obs encoding for {key!r}")


def read_obs_value(group: h5py.Group, key: str, index: int):
    return decode(read_obs_values(group, key, index, index + 1)[0])


def dataset_length(node: h5py.Dataset | h5py.Group) -> int:
    if isinstance(node, h5py.Dataset):
        return int(node.shape[0])
    if isinstance(node, h5py.Group) and "codes" in node:
        return int(node["codes"].shape[0])
    raise TypeError(f"Cannot determine AnnData column length for {type(node).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bounded local preview from the MERFISH H5AD.")
    parser.add_argument("h5ad", type=Path)
    parser.add_argument("--region", default="palm", help="Case-insensitive search term across selected obs fields")
    parser.add_argument("--sample-id", help="Exact sample_id to extract; overrides --region matching")
    parser.add_argument("--anatomic-site", help="Exact anatomic_site to extract")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--list-regions", action="store_true")
    parser.add_argument("--list-samples", action="store_true")
    parser.add_argument("--search-all-obs", action="store_true")
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

        total = dataset_length(obs["cell_id"])
        site_counts: Counter[str] = Counter()
        region_counts: Counter[str] = Counter()
        sample_counts: Counter[tuple[str, str, str, str]] = Counter()
        search_fields = list(obs.keys()) if args.search_all_obs else [k for k in SEARCH_FIELDS if k in obs]
        matches: list[int] = []
        matched_fields: Counter[str] = Counter()
        needle = args.region.strip().lower() if args.region else ""
        target_sample = args.sample_id.strip() if args.sample_id else None
        target_site = args.anatomic_site.strip().lower() if args.anatomic_site else None

        for start in range(0, total, 5000):
            stop = min(total, start + 5000)
            sites = read_obs_values(obs, "anatomic_site", start, stop)
            regions = read_obs_values(obs, "region_name", start, stop)
            samples = read_obs_values(obs, "sample_id", start, stop)
            barcodes = read_obs_values(obs, "sample_barcode", start, stop) if "sample_barcode" in obs else np.array([None] * len(sites), dtype=object)
            runs = read_obs_values(obs, "run_name", start, stop) if "run_name" in obs else np.array([None] * len(sites), dtype=object)

            for site, region, sample, barcode, run_name in zip(sites, regions, samples, barcodes, runs):
                site_text = str(decode(site) or "")
                region_text = str(decode(region) or "")
                sample_text = str(decode(sample) or "")
                sample_counts[(sample_text, str(decode(barcode) or ""), str(decode(run_name) or ""), site_text)] += 1
                site_counts[site_text] += 1
                region_counts[region_text] += 1

            if target_sample:
                for offset, value in enumerate(samples):
                    if str(decode(value) or "") == target_sample:
                        matches.append(start + offset)
                        matched_fields["sample_id"] += 1
            elif target_site:
                for offset, value in enumerate(sites):
                    if str(decode(value) or "").lower() == target_site:
                        matches.append(start + offset)
                        matched_fields["anatomic_site"] += 1
            elif needle:
                row_hits: set[int] = set()
                for field in search_fields:
                    values = read_obs_values(obs, field, start, stop)
                    for offset, value in enumerate(values):
                        if needle in str(decode(value) or "").lower():
                            row_hits.add(start + offset)
                            matched_fields[field] += 1
                matches.extend(sorted(row_hits))
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
            for (sample_id, sample_barcode, run_name, site), count in sorted(sample_counts.items(), key=lambda x: (-x[1], x[0])):
                print(f"{count:>7} | {sample_id} | {sample_barcode} | {run_name} | {site}")
            return 0

        matches = matches[: args.limit]
        if not matches:
            query = f"sample_id={target_sample!r}" if target_sample else f"anatomic_site={args.anatomic_site!r}" if target_site else f"search term={args.region!r}"
            print(f"No cells matched {query}.")
            print("Observed anatomic_site labels:")
            for label, count in site_counts.most_common(20):
                print(f"  {count:>7}  {label}")
            print("Tip: use --list-samples and then --sample-id, or --anatomic-site, for an exact extract.")
            raise SystemExit(2)

        spatial = obsm["spatial"]
        rows: list[dict[str, object]] = []
        for index in matches:
            point = np.asarray(spatial[index]).reshape(-1)
            row = {key: read_obs_value(obs, key, index) for key in REQUIRED_OBS}
            row["index"] = int(index)
            row["spatial"] = [float(point[0]), float(point[1])] if point.size >= 2 else []
            rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sourceId": "human-skin-spatial-census",
        "sourceFile": args.h5ad.name,
        "region": args.region,
        "sampleId": target_sample,
        "anatomicSite": args.anatomic_site,
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
