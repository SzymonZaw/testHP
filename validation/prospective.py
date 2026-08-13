"""Reproducible prospective-validation metadata primitives."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CohortDefinition:
    cohort_id: str
    inclusion: str
    exclusion: str
    target_population: str


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    cohort: CohortDefinition
    primary_endpoint: str
    dataset_version: str
    model_version: str
    preregistered: bool = False


@dataclass(frozen=True)
class AuditRecord:
    experiment_id: str
    status: str
    notes: Optional[str] = None


class ProspectiveValidationRegistry:
    def __init__(self) -> None:
        self._experiments: dict[str, ExperimentSpec] = {}
        self._audits: list[AuditRecord] = []

    def register(self, experiment: ExperimentSpec) -> None:
        if experiment.experiment_id in self._experiments:
            raise ValueError("experiment already registered")
        self._experiments[experiment.experiment_id] = experiment

    def record_audit(self, record: AuditRecord) -> None:
        if record.experiment_id not in self._experiments:
            raise KeyError(record.experiment_id)
        self._audits.append(record)

    def get(self, experiment_id: str) -> ExperimentSpec:
        return self._experiments[experiment_id]
