"""Combine modality-specific states into one biological state."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from core.biological_state import BiologicalState


class MultimodalState:
    """Aggregated state with provenance preserved for every modality."""

    def __init__(self, subject_id: str, timepoint_id: str) -> None:
        self.state = BiologicalState(
            subject_id=subject_id,
            timepoint_id=timepoint_id,
            metadata={"pipeline": "multimodal"},
        )
        self.modalities: dict[str, BiologicalState] = {}

    def add_state(self, modality: str, state: BiologicalState) -> None:
        if state.subject_id != self.state.subject_id:
            raise ValueError("All modality states must belong to the same subject")
        if state.timepoint_id != self.state.timepoint_id:
            raise ValueError("All modality states must use the same timepoint")
        if not modality.strip():
            raise ValueError("modality cannot be empty")
        self.modalities[modality] = deepcopy(state)
        for observation in state.observations:
            self.state.add_observation(observation)
        for name, value in state.dimensions.items():
            self.state.set_dimension(f"{modality}.{name}", value)

    @property
    def modality_names(self) -> list[str]:
        return sorted(self.modalities)

    def summary(self) -> dict:
        return {
            "subject_id": self.state.subject_id,
            "timepoint_id": self.state.timepoint_id,
            "modalities": self.modality_names,
            "observation_count": len(self.state.observations),
            "dimensions": dict(self.state.dimensions),
        }


def fuse_states(states: Iterable[tuple[str, BiologicalState]]) -> MultimodalState:
    """Fuse cell/tissue/RNA/etc. states without discarding their provenance."""
    items = list(states)
    if not items:
        raise ValueError("At least one modality state is required")
    modality, first = items[0]
    fused = MultimodalState(first.subject_id, first.timepoint_id)
    for modality, state in items:
        fused.add_state(modality, state)
    return fused
