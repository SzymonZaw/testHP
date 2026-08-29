from __future__ import annotations

"""Non-diagnostic pathology signal primitives for the cell twin layer."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PathologySignal:
    signal_id: str
    cell_id: str
    category: str
    severity: float | None
    confidence: float | None
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None
    findings: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.signal_id or not self.cell_id or not self.category:
            raise ValueError("pathology signal identity is required")
        for name, value in (("severity", self.severity), ("confidence", self.confidence)):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


def build_pathology_signal(**kwargs: Any) -> PathologySignal:
    result = PathologySignal(**kwargs)
    result.validate()
    return result
