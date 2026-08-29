"""Training-sample and feature-extraction contracts for ML pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .cell_observation import CellObservation
from .ml_contracts import ModelInput


@dataclass(frozen=True)
class TrainingSample:
    """One leakage-safe supervised learning sample."""

    sample_id: str
    observation_id: str
    subject_id: str
    target: Any
    split: str
    label_source_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name, value in (("sample_id", self.sample_id), ("observation_id", self.observation_id), ("subject_id", self.subject_id), ("split", self.split)):
            if not value:
                raise ValueError(f"{name} is required")
        if self.split not in {"train", "validation", "test"}:
            raise ValueError("split must be train, validation, or test")
        if len(set(self.label_source_ids)) != len(self.label_source_ids):
            raise ValueError("label_source_ids must be unique")


@dataclass(frozen=True)
class Dataset:
    """Collection of samples with a subject-aware split policy."""

    dataset_id: str
    samples: tuple[TrainingSample, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.dataset_id:
            raise ValueError("dataset_id is required")
        ids = [sample.sample_id for sample in self.samples]
        if len(ids) != len(set(ids)):
            raise ValueError("sample_id values must be unique")
        subject_splits: dict[str, set[str]] = {}
        for sample in self.samples:
            sample.validate()
            subject_splits.setdefault(sample.subject_id, set()).add(sample.split)
        leaked = {subject for subject, splits in subject_splits.items() if len(splits) > 1}
        if leaked:
            raise ValueError(f"subjects cannot occur in multiple splits: {sorted(leaked)}")


class FeatureExtractor(Protocol):
    """Protocol for converting observations into model inputs."""

    extractor_id: str
    extractor_version: str

    def extract(self, observation: CellObservation) -> ModelInput:
        ...


def default_feature_extractor(observation: CellObservation) -> ModelInput:
    """Baseline extractor preserving all typed observation feature groups."""
    observation.validate()
    features: dict[str, Any] = {}
    for group_name, values in (
        ("morphology", observation.morphology),
        ("molecular", observation.molecular_features),
        ("functional", observation.functional_features),
    ):
        for key, value in values.items():
            features[f"{group_name}.{key}"] = value
    return ModelInput(
        sample_id=observation.observation_id,
        modality=observation.modality,
        features=features,
        spatial_reference=observation.spatial_reference,
        quality=observation.quality,
        metadata={"extractor_id": "default", "extractor_version": "0.1.0", "cell_id": observation.cell_id},
    )
