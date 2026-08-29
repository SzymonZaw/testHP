from __future__ import annotations

"""Whole-body expansion contracts. Hand remains the first-class implementation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OrganSystemReference:
    system_id: str
    name: str
    status: str = "not_implemented"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WholeBodyTwin:
    subject_id: str
    primary_site: str
    organ_systems: tuple[OrganSystemReference, ...] = ()
    version: str = "1"

    def validate(self) -> None:
        if not self.subject_id or not self.primary_site:
            raise ValueError("whole-body twin requires subject and primary site")
        if self.primary_site != "hand":
            raise ValueError("hand is the current implementation boundary")
