from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgeEstimate:
    """Container for a biological-age model output, not a clinical claim."""

    target_id: str
    chronological_age_years: float | None
    estimated_biological_age_years: float | None
    uncertainty_low: float | None
    uncertainty_high: float | None
    model_id: str
    model_version: str
    evidence_ids: tuple[str, ...]
    status: str
    limitations: tuple[str, ...]


def unavailable_age(target_id: str, reason: str = "No validated age model/evidence is available") -> AgeEstimate:
    return AgeEstimate(
        target_id=target_id,
        chronological_age_years=None,
        estimated_biological_age_years=None,
        uncertainty_low=None,
        uncertainty_high=None,
        model_id="none",
        model_version="none",
        evidence_ids=(),
        status="unavailable",
        limitations=(reason, "This prototype must not fabricate a biological-age value."),
    )


def validate_age_output(payload: dict[str, Any]) -> None:
    """Reject impossible/overconfident model payloads at the contract boundary."""
    if payload.get("status") == "available":
        if payload.get("estimated_biological_age_years") is None:
            raise ValueError("available age estimate requires a numeric estimate")
        if not payload.get("model_id") or not payload.get("model_version"):
            raise ValueError("available age estimate requires model identity")
        if not payload.get("evidence_ids"):
            raise ValueError("available age estimate requires evidence IDs")
