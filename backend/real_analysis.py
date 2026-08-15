"""Evidence-backed descriptive analyses for files that are actually available.

These routines deliberately stop at measurements supported by the local input.
They do not emit diagnostic labels, probabilities, or biological claims.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import json
import math


def image_analysis(path: Path) -> dict[str, Any] | None:
    try:
        from PIL import Image, ImageStat
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            stat = ImageStat.Stat(rgb)
            means = [round(float(x), 4) for x in stat.mean]
            brightness = round(sum(means) / 3, 4)
            return {
                "kind": "image_descriptive",
                "file": path.name,
                "width": im.width,
                "height": im.height,
                "mean_r": means[0],
                "mean_g": means[1],
                "mean_b": means[2],
                "mean_brightness": brightness,
            }
    except Exception:
        return None


def tabular_analysis(path: Path, max_rows: int = 50000) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters="\t,;|")
            except csv.Error:
                dialect = csv.excel_tab
            reader = csv.reader(f, dialect)
            rows = []
            numeric = []
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                if not any(cell.strip() for cell in row):
                    continue
                rows.append(row)
                for cell in row:
                    try:
                        value = float(cell.strip())
                        if math.isfinite(value):
                            numeric.append(value)
                    except (ValueError, TypeError):
                        pass
            return {
                "kind": "tabular_descriptive",
                "file": path.name,
                "rows_inspected": len(rows),
                "numeric_values": len(numeric),
                "numeric_min": min(numeric) if numeric else None,
                "numeric_max": max(numeric) if numeric else None,
                "numeric_mean": (sum(numeric) / len(numeric)) if numeric else None,
            }
    except Exception:
        return None


def json_structure_analysis(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None

    def count_nodes(value: Any) -> int:
        if isinstance(value, dict):
            return 1 + sum(count_nodes(v) for v in value.values())
        if isinstance(value, list):
            return sum(count_nodes(v) for v in value)
        return 0

    return {
        "kind": "json_structure",
        "file": path.name,
        "top_level_type": type(data).__name__,
        "structured_nodes": count_nodes(data),
    }
