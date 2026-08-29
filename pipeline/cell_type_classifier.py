"""Pluggable cell-type classification contract.

The project must not infer a biological cell type from morphology alone unless a
validated model is explicitly supplied. This module defines the adapter boundary
for such models and a conservative label normalizer for externally supplied
reference predictions.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass(frozen=True)
class CellTypePrediction:
    cell_id: int
    label: str
    confidence: float
    model_id: str
    model_version: str
    evidence: list[str]


def normalize_predictions(
    predictions: Iterable[dict[str, Any]],
    *,
    model_id: str,
    model_version: str,
    min_confidence: float = 0.80,
) -> list[dict[str, Any]]:
    """Accept predictions from a validated external classifier.

    Predictions below ``min_confidence`` remain explicitly unresolved instead
    of being forced into a cell type. The classifier itself is intentionally
    outside this module so model choice and validation can be versioned.
    """
    if not model_id or not model_version:
        raise ValueError("model_id and model_version are required")
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    result: list[dict[str, Any]] = []
    for item in predictions:
        cell_id = int(item["cell_id"])
        label = str(item.get("label", "not_established"))
        confidence = float(item.get("confidence", 0.0))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("prediction confidence must be between 0 and 1")
        if confidence < min_confidence:
            label = "not_established"
        result.append(asdict(CellTypePrediction(
            cell_id=cell_id,
            label=label,
            confidence=confidence,
            model_id=model_id,
            model_version=model_version,
            evidence=[str(x) for x in item.get("evidence", [])],
        )))
    return result


def classifier_status(predictions: Iterable[dict[str, Any]]) -> str:
    """Return an auditable status for a prediction collection."""
    items = list(predictions)
    if not items:
        return "not_established"
    if any(item.get("label") == "not_established" for item in items):
        return "partially_established"
    return "established_with_validated_classifier"
