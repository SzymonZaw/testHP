"""Technology-neutral real-data pipeline for ML experiments.

The module defines explicit contracts for image/omics inputs, preprocessing,
feature extraction, labels and leakage-safe datasets. It does not depend on
a specific ML framework.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .cell_observation import CellObservation
from .ml_contracts import ModelInput


@dataclass(frozen=True)
class ImageInput:
    """Reference to an image acquisition and its spatial/calibration metadata."""

    data_id: str
    uri: str
    format: str
    width: int
    height: int
    channels: int = 1
    pixel_size_um: float | None = None
    bit_depth: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.data_id or not self.uri or not self.format:
            raise ValueError("image identity and uri are required")
        if self.width <= 0 or self.height <= 0 or self.channels <= 0:
            raise ValueError("image dimensions and channels must be positive")
        if self.pixel_size_um is not None and self.pixel_size_um <= 0:
            raise ValueError("pixel_size_um must be positive")
        if self.bit_depth is not None and self.bit_depth <= 0:
            raise ValueError("bit_depth must be positive")


@dataclass(frozen=True)
class OmicsInput:
    """Reference to molecular measurements associated with an observation."""

    data_id: str
    uri: str
    assay: str
    feature_names: tuple[str, ...] = ()
    values: Mapping[str, float] = field(default_factory=dict)
    units: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.data_id or not self.uri or not self.assay:
            raise ValueError("omics identity, uri and assay are required")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature_names must be unique")
        for name, value in self.values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"omics value for {name!r} must be numeric")


@dataclass(frozen=True)
class PreprocessingSpec:
    """Reproducible preprocessing configuration recorded with a model input."""

    preprocessing_id: str
    version: str
    operations: tuple[str, ...]
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.preprocessing_id or not self.version:
            raise ValueError("preprocessing identity is required")
        if not self.operations:
            raise ValueError("at least one preprocessing operation is required")


@dataclass(frozen=True)
class ProcessedCellData:
    """Output of preprocessing before feature extraction."""

    observation_id: str
    source_data_ids: tuple[str, ...]
    tensors: Mapping[str, Any] = field(default_factory=dict)
    scalar_features: Mapping[str, float] = field(default_factory=dict)
    quality_flags: tuple[str, ...] = ()
    preprocessing: PreprocessingSpec | None = None

    def validate(self) -> None:
        if not self.observation_id or not self.source_data_ids:
            raise ValueError("processed data requires observation and source data")
        if self.preprocessing is not None:
            self.preprocessing.validate()
        for name, value in self.scalar_features.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"scalar feature {name!r} must be numeric")


class Preprocessor(Protocol):
    preprocessing_id: str
    preprocessing_version: str

    def process(
        self,
        observation: CellObservation,
        *,
        images: Sequence[ImageInput] = (),
        omics: Sequence[OmicsInput] = (),
    ) -> ProcessedCellData:
        ...


class RealFeatureExtractor(Protocol):
    extractor_id: str
    extractor_version: str

    def extract(self, processed: ProcessedCellData) -> ModelInput:
        ...


@dataclass(frozen=True)
class DatasetLabel:
    """Ground-truth label with explicit source and optional annotator metadata."""

    label_id: str
    task: str
    value: Any
    source_ids: tuple[str, ...]
    annotator: str | None = None
    confidence: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.label_id or not self.task or not self.source_ids:
            raise ValueError("label identity, task and source_ids are required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("label confidence must be between 0 and 1")


@dataclass(frozen=True)
class RealDatasetSample:
    """Dataset row linking an observation to a ground-truth label."""

    sample_id: str
    observation_id: str
    subject_id: str
    label: DatasetLabel
    split: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.sample_id or not self.observation_id or not self.subject_id:
            raise ValueError("sample identity is required")
        if self.split not in {"train", "validation", "test"}:
            raise ValueError("split must be train, validation, or test")
        self.label.validate()


@dataclass(frozen=True)
class RealDataset:
    """Leakage-safe collection of real samples."""

    dataset_id: str
    version: str
    samples: tuple[RealDatasetSample, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.dataset_id or not self.version:
            raise ValueError("dataset identity is required")
        sample_ids = [sample.sample_id for sample in self.samples]
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("sample_id values must be unique")
        subject_splits: dict[str, set[str]] = {}
        for sample in self.samples:
            sample.validate()
            subject_splits.setdefault(sample.subject_id, set()).add(sample.split)
        leaked = sorted(subject for subject, splits in subject_splits.items() if len(splits) > 1)
        if leaked:
            raise ValueError(f"subjects cannot occur in multiple splits: {leaked}")


class BaselinePreprocessor:
    """Framework-free baseline that validates and records source modalities."""

    preprocessing_id = "baseline-preprocessing"
    preprocessing_version = "0.1.0"

    def process(self, observation: CellObservation, *, images: Sequence[ImageInput] = (), omics: Sequence[OmicsInput] = ()) -> ProcessedCellData:
        observation.validate()
        for image in images:
            image.validate()
        for item in omics:
            item.validate()
        source_ids = tuple(dict.fromkeys((*observation.source_data_ids, *(item.data_id for item in images), *(item.data_id for item in omics))))
        scalar_features: dict[str, float] = {}
        for group in (observation.measurements, observation.morphology, observation.molecular_features, observation.functional_features):
            for name, value in group.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    scalar_features[name] = float(value)
        return ProcessedCellData(
            observation_id=observation.observation_id,
            source_data_ids=source_ids,
            scalar_features=scalar_features,
            quality_flags=(),
            preprocessing=PreprocessingSpec(
                preprocessing_id=self.preprocessing_id,
                version=self.preprocessing_version,
                operations=("validate", "collect_numeric_features"),
            ),
        )


class BaselineRealFeatureExtractor:
    """Converts processed scalar features into the existing ModelInput contract."""

    extractor_id = "baseline-real-features"
    extractor_version = "0.1.0"

    def extract(self, processed: ProcessedCellData) -> ModelInput:
        processed.validate()
        model_input = ModelInput(
            sample_id=processed.observation_id,
            modality="multimodal" if len(processed.source_data_ids) > 1 else "cell",
            features=dict(processed.scalar_features),
            metadata={
                "feature_extractor_id": self.extractor_id,
                "feature_extractor_version": self.extractor_version,
                "preprocessing": processed.preprocessing.preprocessing_id if processed.preprocessing else None,
                "preprocessing_version": processed.preprocessing.version if processed.preprocessing else None,
                "quality_flags": processed.quality_flags,
                "source_data_ids": processed.source_data_ids,
            },
        )
        model_input.validate()
        return model_input
