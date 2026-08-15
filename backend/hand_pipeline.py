"""End-to-end personal hand pipeline for stages 21-25.

The module connects the existing own-cohort vision analyzer to the core
measurement/quality/anatomy models and the longitudinal Digital Biological
Twin. It deliberately stops at evidence and change measurements: it does
not diagnose disease or estimate biological/cellular age.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.anatomy import AnatomicalLocation
from core.biomarker import Biomarker
from core.measurement import Measurement
from core.quality import MeasurementQualityEngine
from core.uncertainty import Uncertainty
from organism.digital_twin import DigitalBiologicalTwin, TwinSnapshot

from .hand_vision import analyze_own_cohort

ZONE_IDS = ("wrist", "palm", "thumb", "index", "middle", "ring", "little")


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quality_score(record: dict[str, Any]) -> tuple[float, tuple[str, ...]]:
    image = record.get("image", {})
    brightness = _safe_float(image.get("mean_brightness"))
    contrast = _safe_float(image.get("contrast"))
    flags: list[str] = []
    score = 1.0
    if brightness is None or not 10 <= brightness <= 245:
        score -= 0.25
        flags.append("extreme_or_missing_brightness")
    if contrast is None or contrast < 5:
        score -= 0.25
        flags.append("low_or_missing_contrast")
    if record.get("hand_count") != 1:
        score -= 0.25
        flags.append("expected_one_hand")
    return max(0.0, round(score, 4)), tuple(flags)


def _location(zone: str) -> AnatomicalLocation:
    return AnatomicalLocation(
        id=f"hand.{zone}",
        name=zone,
        level="site",
        parent_id="hand",
    )


def _measurement(
    subject_id: str,
    timepoint_id: str,
    modality: str,
    metric: str,
    value: Any,
    unit: str | None,
    source: str,
    zone: str,
    confidence: float | None,
    quality_score: float,
    quality_flags: tuple[str, ...],
    index: int,
) -> Measurement:
    biomarker = Biomarker(
        id=f"hand.{metric}",
        name=metric,
        category="hand_observation",
        unit=unit,
        description="Directly measured hand observation; not a biological interpretation.",
    )
    uncertainty = Uncertainty(
        confidence=confidence,
        quality_score=quality_score,
        quality_flags=quality_flags,
    )
    return Measurement(
        id=f"{subject_id}:{timepoint_id}:hand:{zone}:{metric}:{index}",
        subject_id=subject_id,
        timepoint_id=timepoint_id,
        modality=modality,
        biomarker=biomarker,
        value=value,
        measured_at=datetime.now(timezone.utc),
        anatomical_location=_location(zone),
        unit=unit,
        uncertainty=uncertainty,
        source=source,
        processing_version="hand-pipeline-v1",
    )


def build_measurements(
    analysis: dict[str, Any],
    subject_id: str,
    timepoint_id: str,
) -> list[Measurement]:
    """Stage 21: convert real own-cohort vision output to core Measurements."""
    measurements: list[Measurement] = []
    counter = 0
    for result in analysis.get("results", []):
        source = result.get("source_file", "")
        quality_score, flags = _quality_score(result)
        image = result.get("image", {})
        base = (
            ("image_width", image.get("width"), "px", "wrist"),
            ("image_height", image.get("height"), "px", "wrist"),
            ("mean_brightness", image.get("mean_brightness"), "0-255", "wrist"),
            ("image_contrast", image.get("contrast"), "0-255", "wrist"),
            ("detected_hand_count", result.get("hand_count"), "count", "wrist"),
        )
        for metric, value, unit, zone in base:
            measurements.append(_measurement(subject_id, timepoint_id, "hand", metric, value, unit, source, zone, None, quality_score, flags, counter))
            counter += 1

        for hand in result.get("hands", []):
            confidence = _safe_float(hand.get("handedness_confidence"))
            hand_quality = min(quality_score, confidence if confidence is not None else quality_score)
            for metric, value, unit in (("bbox_area_ratio", hand.get("bbox", {}).get("area_ratio"), "normalized_area"), ("landmark_count", len(hand.get("landmarks", [])), "count")):
                measurements.append(_measurement(subject_id, timepoint_id, "hand", metric, value, unit, source, "wrist", confidence, hand_quality, flags, counter))
                counter += 1
            for zone, metrics in hand.get("zones", {}).items():
                for metric, value in metrics.items():
                    unit = "normalized_3d" if metric == "centerline_length_3d_norm" else "normalized"
                    measurements.append(_measurement(subject_id, timepoint_id, "hand", metric, value, unit, source, zone, confidence, hand_quality, flags, counter))
                    counter += 1
    return measurements


def quality_report(measurements: list[Measurement]) -> list[dict[str, Any]]:
    """Stage 22: assess measurements with transparent quality rules."""
    engine = MeasurementQualityEngine()
    report: list[dict[str, Any]] = []
    for measurement in measurements:
        assessment = engine.assess_measurement(measurement)
        report.append({
            "measurement_id": measurement.id,
            "score": assessment.score,
            "usable": assessment.usable,
            "flags": list(assessment.flags),
        })
    return report


def zone_map(measurements: list[Measurement]) -> dict[str, dict[str, Any]]:
    """Stage 23: create a stable spatial map; no abnormality ranking is inferred."""
    zones: dict[str, dict[str, Any]] = {
        zone: {"id": f"hand.{zone}", "level": "site", "parent": "hand", "measurements": []}
        for zone in ZONE_IDS
    }
    for measurement in measurements:
        zone = measurement.anatomical_location.name if measurement.anatomical_location else "wrist"
        if zone not in zones:
            continue
        zones[zone]["measurements"].append(measurement.id)
    return zones


def build_twin(
    subject_id: str,
    timepoint_id: str,
    measurements: list[Measurement],
    quality: list[dict[str, Any]],
) -> DigitalBiologicalTwin:
    """Stage 23: attach the evidence to one immutable twin snapshot."""
    state = {
        "biological_level": "macroscopic",
        "result_type": "observed_measurements",
        "zones": zone_map(measurements),
        "measurements": [asdict(item) for item in measurements],
        "quality": quality,
        "interpretation": {
            "disease": "not_available",
            "ageing": "not_available",
            "cellular_age": "not_available",
        },
        "evidence_boundary": "macroscopic observations only; no disease or biological-age inference",
    }
    twin = DigitalBiologicalTwin(subject_id=subject_id)
    twin.add_snapshot(TwinSnapshot(
        timepoint_id=timepoint_id,
        captured_at=datetime.now(timezone.utc),
        state=state,
        provenance=tuple(sorted({m.source for m in measurements if m.source})),
        uncertainty=quality,
    ))
    return twin


def longitudinal_changes(
    baseline: list[Measurement],
    current: list[Measurement],
) -> list[dict[str, Any]]:
    """Stage 24: compare the same explicit subject/zone/metric across timepoints."""
    current_by_key = {
        (m.anatomical_location.id if m.anatomical_location else "hand.wrist", m.biomarker.id): m
        for m in current
        if _safe_float(m.value) is not None
    }
    changes: list[dict[str, Any]] = []
    for old in baseline:
        old_value = _safe_float(old.value)
        if old_value is None:
            continue
        key = (old.anatomical_location.id if old.anatomical_location else "hand.wrist", old.biomarker.id)
        new = current_by_key.get(key)
        new_value = _safe_float(new.value) if new else None
        if new_value is None:
            continue
        delta = new_value - old_value
        relative = None if old_value == 0 else delta / abs(old_value)
        changes.append({
            "zone": old.anatomical_location.name if old.anatomical_location else "wrist",
            "metric": old.biomarker.name,
            "baseline_timepoint": old.timepoint_id,
            "current_timepoint": new.timepoint_id,
            "baseline": old_value,
            "current": new_value,
            "absolute_change": round(delta, 8),
            "relative_change": round(relative, 8) if relative is not None else None,
            "result_type": "observed_change",
            "interpretation": "not established",
        })
    return changes


def run_hand_pipeline(
    root: str | Path,
    subject_id: str,
    session_id: str,
    timepoint_id: str,
    baseline_measurements: list[Measurement] | None = None,
) -> dict[str, Any]:
    """Stages 21-25 in one reproducible call."""
    analysis = analyze_own_cohort(root)
    measurements = build_measurements(analysis, subject_id, timepoint_id)
    quality = quality_report(measurements)
    twin = build_twin(subject_id, timepoint_id, measurements, quality)
    changes = longitudinal_changes(baseline_measurements or [], measurements)

    return {
        "pipeline_version": "hand-stages-21-25-v1",
        "subject_id": subject_id,
        "session_id": session_id,
        "timepoint_id": timepoint_id,
        "stages": {
            "21_core_observation_integration": "completed",
            "22_quality_and_uncertainty": "completed",
            "23_spatial_zones_and_twin": "completed",
            "24_longitudinal_change": "completed" if baseline_measurements else "inactive_no_baseline",
            "25_research_run_contract": "completed",
        },
        "analysis": analysis,
        "measurements": [asdict(item) for item in measurements],
        "quality": quality,
        "zone_map": zone_map(measurements),
        "digital_twin": {
            "subject_id": twin.subject_id,
            "snapshot_count": len(twin.history()),
            "latest_timepoint": twin.latest().timepoint_id if twin.latest() else None,
            "provenance": list(twin.provenance()),
            "state": twin.latest().state if twin.latest() else None,
        },
        "longitudinal_changes": changes,
        "result_boundary": {
            "observations": "available",
            "derived_change": "available only with explicit baseline/current measurements",
            "disease": "not_available",
            "ageing": "not_available",
            "cellular_age": "not_available",
        },
    }
