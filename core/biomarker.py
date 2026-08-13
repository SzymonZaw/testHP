"""Definitions of measurable biological features."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Biomarker:
    id: str
    name: str
    category: str
    unit: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Biomarker id cannot be empty")
        if not self.name.strip():
            raise ValueError("Biomarker name cannot be empty")
