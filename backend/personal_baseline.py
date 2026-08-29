from __future__ import annotations

"""Longitudinal personal baseline primitives."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BaselineFeature:
    name: str
    value: float
    unit: str | None = None


@dataclass(frozen=True)
class PersonalBaseline:
    subject_id: str
    spatial_id: str
    features: tuple[BaselineFeature, ...]
    source_timepoints: tuple[str, ...]
    method: str
    confidence: float | None = None

    def validate(self) -> None:
        if not self.subject_id or not self.spatial_id or not self.source_timepoints:
            raise ValueError("personal baseline requires subject, spatial target and timepoints")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("baseline confidence must be between 0 and 1")
