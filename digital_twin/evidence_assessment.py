"""Derive a conservative cell assessment from raw evidence."""
from __future__ import annotations

from typing import Any, Dict, Iterable


def summarize_evidence(evidence: Iterable[Any]) -> Dict[str, Any]:
    items = list(evidence)
    if not items:
        return {"evidence_count": 0, "quality": None, "confidence": None, "uncertainty": None, "provenance": []}

    weights = [max(0.0, min(1.0, float(getattr(item, "confidence", 0.0)))) for item in items]
    qualities = [getattr(item, "quality", None) for item in items]
    quality_values = [float(value) for value in qualities if value is not None]
    total = sum(weights)
    confidence = total / len(items) if items else 0.0
    quality = sum(quality_values) / len(quality_values) if quality_values else None
    return {
        "evidence_count": len(items),
        "quality": quality,
        "confidence": confidence,
        "uncertainty": 1.0 - confidence,
        "provenance": [getattr(item, "provenance", None) for item in items if getattr(item, "provenance", None)],
    }


def assessment_inputs(evidence: Iterable[Any]) -> Dict[str, Any]:
    """Return normalized inputs without inventing a health or age conclusion."""
    summary = summarize_evidence(evidence)
    features: Dict[str, list] = {}
    for item in evidence:
        features.setdefault(getattr(item, "feature", "unknown"), []).append(getattr(item, "value", None))
    summary["features"] = features
    summary["assessment_ready"] = bool(summary["evidence_count"] and summary["confidence"] is not None)
    return summary
