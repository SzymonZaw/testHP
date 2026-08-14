"""Dependency-light content preprocessing used by the common normalization layer."""
from __future__ import annotations

import csv
from pathlib import Path

from integration.observation_to_twin import Observation

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def preprocess_content(dataset: str, modality: str, path: Path) -> tuple[Observation, ...]:
    """Extract deterministic, non-ML content facts without loading huge files."""
    observations: list[Observation] = []
    if modality == "image":
        images = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        readable = 0
        for image in images:
            try:
                with image.open("rb") as fh:
                    header = fh.read(16)
                if header.startswith(b"\x89PNG") or header.startswith(b"\xff\xd8"):
                    readable += 1
            except OSError:
                pass
        if images:
            observations.append(Observation(f"preprocess.{dataset}.readable_raster_count", float(readable), readable / len(images), modality))
    elif modality == "rna":
        tables = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".tsv"}]
        rows = 0
        parsed = 0
        for table in tables:
            try:
                with table.open("r", encoding="utf-8", newline="") as fh:
                    reader = csv.reader(fh, delimiter="\t" if table.suffix.lower() == ".tsv" else ",")
                    next(reader, None)
                    rows += sum(1 for _ in reader)
                parsed += 1
            except (OSError, UnicodeError, csv.Error):
                pass
        if tables:
            observations.append(Observation(f"preprocess.{dataset}.parsed_expression_tables", float(parsed), parsed / len(tables), modality))
            observations.append(Observation(f"preprocess.{dataset}.expression_rows", float(rows), 1.0 if parsed else 0.0, modality))
    elif modality == "wsi":
        slides = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".svs", ".ndpi", ".mrxs", ".tif", ".tiff", ".dcm"}]
        if slides:
            observations.append(Observation(f"preprocess.{dataset}.slide_count", float(len(slides)), 1.0, modality))
    return tuple(observations)
