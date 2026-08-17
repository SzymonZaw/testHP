from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib

from PIL import Image, ImageStat

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
SKIN_CATEGORIES = {"normal_skin", "aging_skin", "lesions", "pathology"}

@dataclass
class SkinObservation:
    asset_id: str
    subject_id: str
    timepoint: str
    category: str
    path: str
    width: int | None
    height: int | None
    brightness: float | None
    contrast: float | None
    status: str
    evidence_level: str = "observed"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _asset_id(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]


def inspect_skin_image(path: Path, subject_id: str = "unknown", timepoint: str = "unknown", category: str | None = None) -> dict[str, Any]:
    category = category or (path.parent.name if path.parent.name in SKIN_CATEGORIES else "unclassified")
    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            stat = ImageStat.Stat(image)
            mean = sum(stat.mean) / 3.0
            std = sum(stat.stddev) / 3.0
            return SkinObservation(_asset_id(path), subject_id, timepoint, category, str(path), image.width, image.height, mean / 255.0, std / 255.0, "available").to_dict()
    except Exception as exc:
        return SkinObservation(_asset_id(path), subject_id, timepoint, category, str(path), None, None, None, None, "unavailable").to_dict() | {"reason": str(exc)}


def scan_skin(root: Path, subject_id: str = "unknown", timepoint: str = "unknown") -> list[dict[str, Any]]:
    if not root.exists():
        return []
    return [inspect_skin_image(p, subject_id, timepoint) for p in sorted(root.rglob("*")) if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]


def validate_skin_dataset(root: Path) -> dict[str, Any]:
    observations = scan_skin(root)
    categories = {c: [x for x in observations if x["category"] == c] for c in SKIN_CATEGORIES}
    duplicates: dict[str, list[str]] = {}
    hashes: dict[str, list[str]] = {}
    for obs in observations:
        try:
            digest = hashlib.sha256(Path(obs["path"]).read_bytes()).hexdigest()
            hashes.setdefault(digest, []).append(obs["path"])
        except OSError:
            pass
    duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}
    return {
        "status": "available" if observations else "unavailable",
        "total_images": len(observations),
        "categories": {k: len(v) for k, v in categories.items()},
        "duplicates": duplicates,
        "warnings": (["duplicate image content detected across files"] if duplicates else []),
        "evidence_level": "observed",
        "diagnosis": "not performed",
    }
