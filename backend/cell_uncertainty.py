from __future__ import annotations

"""Common uncertainty/confidence representation for cell-level outputs."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UncertainValue:
    value: Any
    confidence: float | None
    lower: float | None = None
    upper: float | None = None
    unit: str | None = None
    method: str | None = None
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError("lower bound cannot exceed upper bound")


def build_uncertain_value(**kwargs: Any) -> UncertainValue:
    result = UncertainValue(**kwargs)
    result.validate()
    return result
