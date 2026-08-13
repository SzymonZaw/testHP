"""Anatomical context used by observations and measurements."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OrganSystem:
    id: str
    name: str


@dataclass(frozen=True)
class Organ:
    id: str
    name: str
    system_id: Optional[str] = None


@dataclass(frozen=True)
class Tissue:
    id: str
    name: str
    organ_id: Optional[str] = None


@dataclass(frozen=True)
class AnatomicalLocation:
    """A location can refer to a system, organ, tissue, or a more precise site."""

    id: str
    name: str
    level: str
    parent_id: Optional[str] = None

    def __post_init__(self) -> None:
        allowed = {"organism", "system", "organ", "tissue", "cell_population", "cell", "site"}
        if self.level not in allowed:
            raise ValueError(f"Unsupported anatomical level: {self.level}")
