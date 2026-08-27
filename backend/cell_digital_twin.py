from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .anatomy_foundation import CellObject
from .biological_state import BiologicalAgeEstimate
from .canonical_cell_state import CanonicalCellState, build_canonical_cell_state
from .cell_observation import CellObservation
from .longitudinal_cells import CellTrajectory


@dataclass(frozen=True)
class CellDigitalTwin:
    """Auditable digital representation of one observed cell."""

    snapshot: CanonicalCellState
    trajectory: CellTrajectory | None = None
    observations: tuple[CellObservation, ...] = ()

    @property
    def cell_id(self) -> str:
        return self.snapshot.cell.cell_id

    @property
    def subject_id(self) -> str:
        return self.snapshot.cell.subject_id

    @property
    def hand_id(self) -> str:
        return self.snapshot.cell.hand_id

    @property
    def timepoint_id(self) -> str:
        return self.snapshot.cell.timepoint_id

    def validate(self) -> None:
        self.snapshot.validate()
        for observation in self.observations:
            observation.validate()
            if not observation.matches_cell(self.snapshot.cell):
                raise ValueError("cell observation identity must match digital twin")
        if self.trajectory is not None:
            if (self.trajectory.cell_id, self.trajectory.subject_id, self.trajectory.hand_id) != (
                self.cell_id, self.subject_id, self.hand_id
            ):
                raise ValueError("cell trajectory identity must match digital twin")
            if not any(point.timepoint_id == self.timepoint_id for point in self.trajectory.points):
                raise ValueError("cell trajectory must contain the snapshot timepoint")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "identity": {
                "cell_id": self.cell_id,
                "subject_id": self.subject_id,
                "hand_id": self.hand_id,
                "tissue_id": self.snapshot.cell.tissue_id,
                "timepoint_id": self.timepoint_id,
            },
            "snapshot": self.snapshot.to_dict(),
            "observations": [observation.to_dict() for observation in self.observations],
            "trajectory": (
                {
                    "cell_id": self.trajectory.cell_id,
                    "subject_id": self.trajectory.subject_id,
                    "hand_id": self.trajectory.hand_id,
                    "points": [
                        {
                            "timepoint_id": point.timepoint_id,
                            "state": point.state,
                            "state_confidence": point.state_confidence,
                            "biological_age_years": point.biological_age_years,
                            "age_interval": point.age_interval,
                        }
                        for point in self.trajectory.points
                    ],
                }
                if self.trajectory is not None
                else None
            ),
        }


def build_cell_digital_twin(
    snapshot: CanonicalCellState,
    *,
    trajectory: CellTrajectory | None = None,
    observations: tuple[CellObservation, ...] = (),
) -> CellDigitalTwin:
    """Build one auditable cell twin from a canonical snapshot."""
    twin = CellDigitalTwin(snapshot=snapshot, trajectory=trajectory, observations=observations)
    twin.validate()
    return twin


def build_cell_digital_twin_from_observation(
    cell: CellObject,
    observation: CellObservation,
    *,
    age_estimate: BiologicalAgeEstimate | None = None,
    trajectory: CellTrajectory | None = None,
) -> CellDigitalTwin:
    """Build a cell twin from a cell observation and preserve the observation."""
    observation.validate()
    if not observation.matches_cell(cell):
        raise ValueError("cell observation must match supplied cell")
    snapshot = build_canonical_cell_state(
        cell,
        state_assessment=observation.assessment,
        age_estimate=age_estimate,
    )
    return build_cell_digital_twin(
        snapshot,
        trajectory=trajectory,
        observations=(observation,),
    )
