"""Evidence-backed aggregation for biological state and spatial summaries.

This module deliberately separates raw observations/evidence from the UI. It only
promotes explicitly supplied, validated interpretation values; absence of evidence
never becomes a biological conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .anatomy import AnatomicalLocation
from .biological_state import BiologicalState
from .evidence import Evidence
from .observation import Observation


BIOLOGICAL_DIMENSIONS = (
    "biological_age",
    "structural_functional_state",
    "damage",
    "pathology",
)


@dataclass(frozen=True)
class EvidenceSummary:
    location_id: str
    evidence_ids: tuple[str, ...]
    count: int
    status: str


class BiologicalStateAggregator:
    """Build a state from observations and their explicitly linked evidence."""

    def __init__(
        self,
        observations: Iterable[Observation],
        evidence: Iterable[Evidence],
        locations: Iterable[AnatomicalLocation],
    ) -> None:
        self.observations = tuple(observations)
        self.evidence = tuple(evidence)
        self.locations = {location.id: location for location in locations}
        self._observations_by_id = {observation.id: observation for observation in self.observations}

    def evidence_for_location(self, location_id: str, *, include_descendants: bool = False) -> tuple[Evidence, ...]:
        """Return only evidence explicitly attached to observations in the scope.

        Descendant aggregation follows the anatomical ``parent_id`` chain. It never
        creates evidence records and never treats an empty descendant as observed.
        """
        scope = {location_id}
        if include_descendants:
            changed = True
            while changed:
                changed = False
                for location in self.locations.values():
                    if location.parent_id in scope and location.id not in scope:
                        scope.add(location.id)
                        changed = True

        result: list[Evidence] = []
        seen: set[str] = set()
        for item in self.evidence:
            observation = self._observations_by_id.get(item.observation_id)
            if observation is None or observation.anatomical_location is None:
                continue
            if observation.anatomical_location.id in scope and item.id not in seen:
                result.append(item)
                seen.add(item.id)
        return tuple(result)

    def summarize_location(self, location_id: str, *, include_descendants: bool = False) -> EvidenceSummary:
        items = self.evidence_for_location(location_id, include_descendants=include_descendants)
        return EvidenceSummary(
            location_id=location_id,
            evidence_ids=tuple(item.id for item in items),
            count=len(items),
            status="observed" if items else "insufficient_evidence",
        )

    def build_state(self, subject_id: str, timepoint_id: str, *, location_id: str | None = None) -> BiologicalState:
        """Build the single state object consumed by higher layers.

        Interpretation values are accepted only from observation metadata under the
        explicit ``validated_interpretations`` key. Values are otherwise unknown.
        """
        state = BiologicalState(subject_id=subject_id, timepoint_id=timepoint_id)
        scoped = [
            observation
            for observation in self.observations
            if observation.subject_id == subject_id and observation.timepoint_id == timepoint_id
        ]
        for observation in scoped:
            if location_id is None or self._observation_in_location(observation, location_id):
                state.add_observation(observation)

        evidence_items = [
            item for item in self.evidence
            if item.subject_id == subject_id
            and item.observation_id in {observation.id for observation in state.observations}
        ]
        state.evidence_ids = tuple(item.id for item in evidence_items)
        state.evidence_count = len(evidence_items)
        state.availability = "observed" if evidence_items else "insufficient_evidence"
        state.confidence = self._confidence(evidence_items)
        state.interpretations = self._interpretations(state.observations, evidence_items)
        return state

    def _observation_in_location(self, observation: Observation, location_id: str) -> bool:
        location = observation.anatomical_location
        while location is not None:
            if location.id == location_id:
                return True
            location = self.locations.get(location.parent_id) if location.parent_id else None
        return False

    @staticmethod
    def _confidence(items: Iterable[Evidence]) -> float | None:
        values = [item.confidence for item in items if item.confidence is not None]
        return sum(values) / len(values) if values else None

    @staticmethod
    def _interpretations(observations: Iterable[Observation], evidence: Iterable[Evidence]) -> Mapping[str, object]:
        evidence_by_observation = {item.observation_id for item in evidence}
        result: dict[str, object] = {}
        for observation in observations:
            if observation.id not in evidence_by_observation:
                continue
            validated = observation.metadata.get("validated_interpretations", {})
            if not isinstance(validated, Mapping):
                continue
            for dimension in BIOLOGICAL_DIMENSIONS:
                if dimension in validated and dimension not in result:
                    result[dimension] = validated[dimension]
        return result
