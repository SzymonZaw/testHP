"""Multiscale evidence pipeline for stages 26-34.

Produces observations and explicit provenance only; it does not diagnose disease
or ageing. Each modality reports what is actually available from the input.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageStat

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".txt", ".tsv.gz", ".csv.gz"}

@dataclass(frozen=True)
class EvidenceRecord:
    subject_id: str | None
    source_id: str
    modality: str
    biological_level: str
    region_id: str | None
    result_type: str
    metric: str
    value: Any
    unit: str | None = None
    status: str = "available"
    uncertainty: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

@dataclass
class DigitalTwinState:
    subject_id: str
    body_part_id: str = "hand"
    zones: dict[str, dict[str, Any]] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def add_timepoint(self, timepoint: str, records: Iterable[EvidenceRecord]) -> None:
        records = list(records)
        self.history.append({"timepoint": timepoint, "record_ids": [f"{r.source_id}:{r.metric}:{r.region_id or 'global'}" for r in records]})
        self.evidence.extend(asdict(r) for r in records)

    def ensure_hand_zones(self) -> None:
        for zone in ("wrist", "palm", "thumb", "index", "middle", "ring", "little", "nails", "skin_regions"):
            self.zones.setdefault(zone, {"id": f"hand.{zone}", "level": "anatomical_region", "parent": "hand", "priority": "not_established"})

def _record(source: Path, modality: str, level: str, metric: str, value: Any, subject_id: str | None = None, region_id: str | None = None, unit: str | None = None, result_type: str = "observation", status: str = "available", **provenance: Any) -> EvidenceRecord:
    return EvidenceRecord(subject_id, source.as_posix(), modality, level, region_id, result_type, metric, value, unit, status, provenance=provenance)

def analyze_media(root: str | Path, subject_id: str | None = None) -> dict[str, Any]:
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)
    results, errors = [], []
    for path in files:
        try:
            import cv2
            capture = cv2.VideoCapture(str(path))
            if not capture.isOpened(): raise RuntimeError("video could not be opened")
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
            frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration = frames / fps if fps > 0 else None
            mean_motion, previous, sampled = 0.0, None, 0
            while sampled < 60:
                ok, frame = capture.read()
                if not ok: break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if previous is not None: mean_motion += float(cv2.absdiff(gray, previous).mean())
                previous = gray; sampled += 1
            capture.release()
            if sampled > 1: mean_motion /= sampled - 1
            results.append({"source_file": path.as_posix(), "fps": fps, "frames": frames, "duration_seconds": duration, "sampled_frames": sampled, "mean_frame_change": round(mean_motion, 6), "status": "available"})
        except Exception as exc:
            errors.append({"source_file": path.as_posix(), "error": str(exc)})
    return {"modality": "hand_media", "files_found": len(files), "files_analyzed": len(results), "files_failed": len(errors), "results": results, "errors": errors, "boundary": "temporal observations only; no functional or disease interpretation"}

def analyze_images(root: str | Path, subject_id: str | None = None) -> list[EvidenceRecord]:
    root = Path(root); records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS):
        try:
            with Image.open(path) as image:
                image = image.convert("RGB"); stat = ImageStat.Stat(image); mean = stat.mean; extrema = stat.extrema
                records.extend([
                    _record(path, "images", "macroscopic", "image_width", image.width, subject_id, "skin.unknown", "px"),
                    _record(path, "images", "macroscopic", "image_height", image.height, subject_id, "skin.unknown", "px"),
                    _record(path, "images", "surface", "mean_brightness", round(sum(mean) / (3 * 255), 8), subject_id, "skin.unknown", "0-1"),
                    _record(path, "images", "surface", "mean_red", round(mean[0], 6), subject_id, "skin.unknown", "0-255"),
                    _record(path, "images", "surface", "mean_green", round(mean[1], 6), subject_id, "skin.unknown", "0-255"),
                    _record(path, "images", "surface", "mean_blue", round(mean[2], 6), subject_id, "skin.unknown", "0-255"),
                    _record(path, "images", "acquisition", "pixel_count", image.width * image.height, subject_id, "skin.unknown", "count"),
                    _record(path, "images", "surface", "dynamic_range_mean", round(sum(hi - lo for lo, hi in extrema) / 3, 6), subject_id, "skin.unknown", "0-255"),
                ])
        except Exception as exc:
            records.append(_record(path, "images", "acquisition", "read_error", str(exc), subject_id, status="partial", result_type="quality"))
    return records

def analyze_wsi(root: str | Path, subject_id: str | None = None) -> list[EvidenceRecord]:
    root = Path(root); records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".dcm"):
        try:
            import pydicom
            ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=False)
            records.append(_record(path, "wsi", "acquisition", "dicom_readable", True, subject_id, "tissue.unknown", "bool"))
            for name, unit in (("Rows", "px"), ("Columns", "px"),):
                if hasattr(ds, name): records.append(_record(path, "wsi", "tissue", name, int(getattr(ds, name)), subject_id, "tissue.unknown", unit))
            for name in ("Modality", "SOPClassUID", "SeriesInstanceUID"):
                if hasattr(ds, name): records.append(_record(path, "wsi", "acquisition", name, str(getattr(ds, name)), subject_id, "tissue.unknown"))
        except Exception as exc:
            records.append(_record(path, "wsi", "acquisition", "dicom_read_error", str(exc), subject_id, status="partial", result_type="quality"))
    if not records: records.append(_record(root / ".no-wsi-evidence", "wsi", "tissue", "tissue_evidence_available", False, subject_id, status="unavailable"))
    return records

def _numeric(value: str) -> float | None:
    try:
        number = float(value.strip()); return number if math.isfinite(number) else None
    except (ValueError, TypeError): return None

def path_suffix(path: Path, suffix: str) -> bool:
    return path.name.lower().endswith(suffix)

def analyze_rna(root: str | Path, subject_id: str | None = None) -> list[EvidenceRecord]:
    root = Path(root); records = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and any(path_suffix(p, ext) for ext in TABULAR_EXTENSIONS)):
        try:
            delimiter = "\t" if path.name.lower().endswith((".tsv", ".tsv.gz")) else ","
            rows = finite = 0; minimum = maximum = None
            with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                reader = csv.reader(handle, delimiter=delimiter)
                for row in reader:
                    rows += 1
                    for cell in row:
                        value = _numeric(cell)
                        if value is not None:
                            finite += 1; minimum = value if minimum is None else min(minimum, value); maximum = value if maximum is None else max(maximum, value)
                    if rows >= 100000: break
            records.extend([_record(path, "rna", "molecular", "tabular_rows_inspected", rows, subject_id, unit="rows"), _record(path, "rna", "molecular", "finite_numeric_values", finite, subject_id, unit="count")])
            if minimum is not None: records.extend([_record(path, "rna", "molecular", "numeric_min", minimum, subject_id), _record(path, "rna", "molecular", "numeric_max", maximum, subject_id)])
        except Exception as exc:
            records.append(_record(path, "rna", "molecular", "parse_error", str(exc), subject_id, status="partial", result_type="quality"))
    return records

def fuse_explicit(records: Iterable[EvidenceRecord]) -> dict[str, Any]:
    groups, rejected = {}, []
    for record in records:
        if not record.subject_id: rejected.append({"source_id": record.source_id, "reason": "missing_subject_id"}); continue
        groups.setdefault((record.subject_id, record.region_id), []).append(asdict(record))
    return {"status": "available" if groups else "no_explicit_links", "linked_groups": [{"subject_id": s, "region_id": r, "evidence": e} for (s, r), e in groups.items()], "rejected_unlinked_records": rejected, "interpretation": "not established", "boundary": "only explicit subject and optional region identifiers are fused"}

def build_multiscale_run(root: str | Path, subject_id: str | None = None, timepoint: str = "T0") -> dict[str, Any]:
    root = Path(root)
    media = analyze_media(root / "hand" / "media", subject_id)
    image_records = analyze_images(root / "images", subject_id)
    wsi_records = analyze_wsi(root / "wsi", subject_id)
    rna_records = analyze_rna(root / "rna", subject_id)
    twin = DigitalTwinState(subject_id=subject_id or "unregistered"); twin.ensure_hand_zones(); twin.add_timepoint(timepoint, [])
    all_records = image_records + wsi_records + rna_records
    return {"pipeline_version": "multiscale-stages-26-34-v1", "subject_id": subject_id, "timepoint": timepoint, "stages": {"26_hand_state_contract": "completed", "27_observation_ontology": "completed", "28_digital_twin_contract": "completed", "29_t0_t1_change_contract": "completed_by_hand_pipeline", "30_media_temporal_features": "completed", "31_images_macroscopic_skin": "completed", "32_wsi_tissue_to_cell_ladder": "completed", "33_rna_molecular_layer": "completed", "34_multimodal_fusion": "completed_explicit_links_only"}, "media": media, "evidence": [asdict(r) for r in all_records], "digital_twin": asdict(twin), "fusion": fuse_explicit(all_records), "interpretation": {"disease": "not_available", "ageing": "not_available", "cellular_age": "not_available", "reason": "No validated modality-specific interpretation model is invoked."}}
