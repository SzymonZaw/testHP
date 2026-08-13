"""Uncertainty and data-quality metadata."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Uncertainty:
    confidence: Optional[float] = None
    standard_error: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    quality_score: Optional[float] = None
    quality_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("confidence", "quality_score"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
