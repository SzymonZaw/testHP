"""Canonical update flow for the longitudinal hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .anatomy_foundation import CellStateAssessment
from .hand_state import HandState
from .hierarchy_mapping import HierarchyMappingRegistry
from .longitudinal_hand_twin import HandObservation, LongitudinalHandTwin
from .multiscale_assessment import MultiscaleAssessment, aggregate_assessments


@dataclass(frozen=True)
class TwinUpdateResult:
    """Auditable result of adding one validated hand observation."""

    observation: HandObservation
    observation_count: int
    latest_biological_age: float | None
    health_trajectory: Any
    multiscale_assessments: tuple[MultiscaleAssessment, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation": {
                "observed_at": self.observation.observed_at,
                "state": self.observation.state.to_dict(),
            },
            "observation_count": self.observation_count,
            "latest_biological_age": self.latest_biological_age,
            "health_trajectory": self.health_trajectory.to_dict(),
            "multiscale_assessments": tuple(item.to_dict() for item in self.multiscale_assessments),
        }


def update_hand_twin(
    twin: LongitudinalHandTwin,
    state: HandState,
    *,
    observed_at: str | None = None,
) -> TwinUpdateResult:
    """Add a hand-level observation and rebuild its longitudinal health state."""
    observation = twin.add_observation(state, observed_at)
    trajectory = twin.health_trajectory()
    return TwinUpdateResult(
        observation=observation,
        observation_count=len(twin.observations),
        latest_biological_age=twin.latest_state.biological_age if twin.latest_state else None,
        health_trajectory=trajectory,
    )


def update_hand_twin_from_cells(
    twin: LongitudinalHandTwin,
    assessments: Iterable[CellStateAssessment],
    hierarchy_mapping: HierarchyMappingRegistry,
    *,
    observed_at: str | None = None,
) -> TwinUpdateResult:
    """Aggregate cell observations and append the resulting hand state.

    The registry is the explicit source of containment relationships. The
    function never guesses missing hierarchy links and does not prescribe
    treatment or rejuvenation actions.
    """
    hierarchy_mapping.validate()
    cell_assessments = tuple(assessments)
    if not cell_assessments:
        raise ValueError("at least one cell assessment is required")
    mappings_by_cell = {item.cell_id: item for item in hierarchy_mapping.mappings}
    missing = [item.cell_id for item in cell_assessments if item.cell_id not in mappings_by_cell]
    if missing:
        raise ValueError(f"missing hierarchy mapping for cells: {', '.join(sorted(missing))}")
    hand_ids = {mappings_by_cell[item.cell_id].hand_id for item in cell_assessments}
    if hand_ids != {twin.hand_id}:
        raise ValueError("cell assessments do not belong to the twin hand")

    aggregated = aggregate_assessments(
        cell_assessments,
        hand_id=twin.hand_id,
        hierarchy_mapping=hierarchy_mapping,
    )
    hand_assessment = next(item for item in aggregated if item.level == "hand")
    state = HandState.from_multiscale_assessment(hand_assessment)
    observation = twin.add_observation(state, observed_at)
    trajectory = twin.health_trajectory()
    return TwinUpdateResult(
        observation=observation,
        observation_count=len(twin.observations),
        latest_biological_age=twin.latest_state.biological_age if twin.latest_state else None,
        health_trajectory=trajectory,
        multiscale_assessments=tuple(aggregated),
    )
