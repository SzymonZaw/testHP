from __future__ import annotations

"""Cell biological-age primitives.

A biological-age estimate is explicitly a model output with uncertainty. This
module does not claim that a particular biomarker is a validated age clock.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CellBiologicalAge:
    estimate_years: float
    confidence: float | None
    reference_population: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    signals: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.estimate_years < 0:
            raise ValueError("biological age cannot be negative")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


def build_biological_age(**kwargs: Any) -> CellBiologicalAge:
    result = CellBiologicalAge(**kwargs)
    result.validate()
    return result
