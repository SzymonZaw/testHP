"""Longitudinal timepoint representation."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Timepoint:
    id: str
    date: date
    label: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Timepoint id cannot be empty")
