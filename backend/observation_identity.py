"""Stable identity and lineage contracts for longitudinal cell observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CellIdentity:
    """Stable identity of a cell across repeated observations."""

    cell_id: str
    subject_id: str
    hand_id: str
    population_id: str | None = None
    tissue_id: str | None = None
    region_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "cell_id": self.cell_id,
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "population_id": self.population_id,
            "tissue_id": self.tissue_id,
            "region_id": self.region_id,
        }


@dataclass(frozen=True)
class ObservationIdentity:
    """Identity of one measurement of a stable cell at one timepoint."""

    observation_id: str
    cell_id: str
    timepoint_id: str
    observed_at: datetime
    evidence_ids: tuple[str, ...] = ()

    def validate_for(self, cell: CellIdentity) -> None:
        if self.cell_id != cell.cell_id:
            raise ValueError("observation cell_id does not match supplied cell identity")

    def to_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id,
            "cell_id": self.cell_id,
            "timepoint_id": self.timepoint_id,
            "observed_at": self.observed_at.isoformat(),
            "evidence_ids": self.evidence_ids,
        }


@dataclass(frozen=True)
class CellLineage:
    """Explicit links connecting observations of one stable cell."""

    cell: CellIdentity
    observations: tuple[ObservationIdentity, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for observation in self.observations:
            observation.validate_for(self.cell)
            if observation.observation_id in seen:
                raise ValueError(f"duplicate observation_id: {observation.observation_id}")
            seen.add(observation.observation_id)

    @property
    def ordered_observations(self) -> tuple[ObservationIdentity, ...]:
        return tuple(sorted(self.observations, key=lambda item: item.observed_at))

    @property
    def observation_ids(self) -> tuple[str, ...]:
        return tuple(item.observation_id for item in self.ordered_observations)

    def to_dict(self) -> dict[str, object]:
        return {
            "cell": self.cell.to_dict(),
            "observation_ids": self.observation_ids,
            "observations": tuple(item.to_dict() for item in self.ordered_observations),
        }
