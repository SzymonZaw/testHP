"""Consistency checks for longitudinal cell observation histories."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .cell_evidence import CellEvidence
from .longitudinal_cells import CellTimepointRecord
from .observation_identity import CellIdentity, ObservationIdentity


@dataclass(frozen=True)
class ConsistencyIssue:
    code: str
    message: str
    observation_id: str | None = None
    timepoint_id: str | None = None


@dataclass(frozen=True)
class ObservationConsistencyReport:
    valid: bool
    issues: tuple[ConsistencyIssue, ...]
    checked_observations: int
    checked_evidence: int

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "issues": tuple(issue.__dict__ for issue in self.issues),
            "checked_observations": self.checked_observations,
            "checked_evidence": self.checked_evidence,
        }


def validate_observation_consistency(
    cell: CellIdentity,
    records: Iterable[CellTimepointRecord],
    observations: Iterable[ObservationIdentity] = (),
) -> ObservationConsistencyReport:
    """Validate identity, temporal ordering, context and evidence lineage.

    This validator is intentionally conservative: inconsistencies are reported rather
    than repaired or silently inferred.
    """
    records = tuple(records)
    observations = tuple(observations)
    issues: list[ConsistencyIssue] = []

    seen_timepoints: set[str] = set()
    seen_observations: set[str] = set()
    last_observed_at: datetime | None = None

    observation_by_id = {item.observation_id: item for item in observations}
    if len(observation_by_id) != len(observations):
        issues.append(ConsistencyIssue("duplicate_observation_identity", "duplicate observation_id in observation identities"))

    for observation in sorted(observations, key=lambda item: item.observed_at):
        if observation.cell_id != cell.cell_id:
            issues.append(ConsistencyIssue("cell_identity_mismatch", "observation belongs to another cell", observation.observation_id, observation.timepoint_id))
        if observation.observation_id in seen_observations:
            issues.append(ConsistencyIssue("duplicate_observation_id", "observation_id occurs more than once", observation.observation_id, observation.timepoint_id))
        seen_observations.add(observation.observation_id)
        if observation.timepoint_id in seen_timepoints:
            issues.append(ConsistencyIssue("duplicate_timepoint_id", "timepoint_id occurs more than once", observation.observation_id, observation.timepoint_id))
        seen_timepoints.add(observation.timepoint_id)
        if last_observed_at is not None and observation.observed_at < last_observed_at:
            issues.append(ConsistencyIssue("non_monotonic_time", "observations are not chronologically ordered", observation.observation_id, observation.timepoint_id))
        last_observed_at = observation.observed_at

    for record in records:
        try:
            record.validate()
        except ValueError as exc:
            issues.append(ConsistencyIssue("invalid_record", str(exc), record.observation_id, record.timepoint_id))
            continue

        if (record.cell_id, record.subject_id, record.hand_id) != (cell.cell_id, cell.subject_id, cell.hand_id):
            issues.append(ConsistencyIssue("context_mismatch", "record subject/hand/cell context does not match CellIdentity", record.observation_id, record.timepoint_id))
        if record.timepoint_id in seen_timepoints and record.observation_id is None:
            issues.append(ConsistencyIssue("unidentified_record", "record has no observation_id for an identified timepoint", None, record.timepoint_id))
        if record.observation_id is not None and record.observation_id in observation_by_id:
            identity = observation_by_id[record.observation_id]
            if identity.timepoint_id != record.timepoint_id:
                issues.append(ConsistencyIssue("observation_timepoint_mismatch", "record and observation identity disagree on timepoint", record.observation_id, record.timepoint_id))

        for evidence in record.evidence:
            if evidence.timepoint_id is not None and evidence.timepoint_id != record.timepoint_id:
                issues.append(ConsistencyIssue("evidence_timepoint_mismatch", "evidence timepoint does not match record", record.observation_id, record.timepoint_id))
            if record.observation_id is not None and evidence.observation_id is not None and evidence.observation_id != record.observation_id:
                issues.append(ConsistencyIssue("evidence_observation_mismatch", "evidence observation does not match record", record.observation_id, record.timepoint_id))

    return ObservationConsistencyReport(
        valid=not issues,
        issues=tuple(issues),
        checked_observations=len(observations),
        checked_evidence=sum(len(record.evidence) for record in records),
    )
