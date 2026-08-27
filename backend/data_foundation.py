from __future__ import annotations

"""Canonical Phase-A data foundation for the hand digital twin.

This module deliberately models provenance and spatial identity without making
clinical or biological interpretations.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
import uuid

SourceClass = Literal["observed", "computed", "default", "simulated"]
RegistrationStatus = Literal["unregistered", "registered", "rejected", "unknown"]
QualityStatus = Literal["unknown", "acceptable", "degraded", "rejected"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class Subject:
    subject_id: str


@dataclass(frozen=True)
class Hand:
    hand_id: str
    subject_id: str
    laterality: Literal["left", "right", "unknown"]


@dataclass(frozen=True)
class Timepoint:
    timepoint_id: str
    subject_id: str
    acquired_at: str | None = None
    age_at_acquisition: float | None = None
    protocol: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Acquisition:
    acquisition_id: str
    subject_id: str
    timepoint_id: str
    source_type: str
    modality: str
    device: str | None = None
    operator: str | None = None
    acquired_at: str | None = None
    protocol: str | None = None
    calibration: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SpatialReference:
    frame_id: str
    registration_status: RegistrationStatus = "unknown"
    anatomical_target: str | None = None
    transform: dict[str, Any] = field(default_factory=dict)
    registration_quality: float | None = None

    def validate(self) -> None:
        if self.registration_quality is not None and not 0 <= self.registration_quality <= 1:
            raise ValueError("registration_quality must be between 0 and 1")
        if self.registration_status == "registered" and not self.transform:
            raise ValueError("registered spatial references require a transform")


@dataclass(frozen=True)
class Quality:
    status: QualityStatus = "unknown"
    score: float | None = None
    flags: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("quality score must be between 0 and 1")


@dataclass(frozen=True)
class Uncertainty:
    kind: str = "unknown"
    score: float | None = None
    interval: tuple[float, float] | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("uncertainty score must be between 0 and 1")
        if self.interval is not None and self.interval[0] > self.interval[1]:
            raise ValueError("uncertainty interval is invalid")


@dataclass(frozen=True)
class Provenance:
    source_object_ids: tuple[str, ...] = ()
    method: str | None = None
    method_version: str | None = None
    processing_timestamp: str | None = None
    validation_status: str = "unknown"
    pipeline_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataObject:
    data_id: str
    data_type: str
    subject_id: str
    timepoint_id: str
    acquisition_id: str
    source_class: SourceClass
    modality: str
    status: str
    quality: Quality
    uncertainty: Uncertainty
    provenance: Provenance
    spatial_reference: SpatialReference
    derived_from: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.source_class == "computed" and not self.provenance.source_object_ids and not self.derived_from:
            raise ValueError("computed data requires source_object_ids or derived_from")
        if self.source_class == "default" and self.derived_from:
            raise ValueError("default data cannot claim derived lineage")
        if self.source_class == "simulated" and not self.metadata.get("simulation"):
            raise ValueError("simulated data must declare simulation metadata")
        self.quality.validate()
        self.uncertainty.validate()
        self.spatial_reference.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def make_subject(subject_id: str) -> Subject:
    return Subject(subject_id=subject_id)


def make_hand(subject_id: str, laterality: Literal["left", "right", "unknown"], hand_id: str | None = None) -> Hand:
    return Hand(hand_id or _id("hand"), subject_id, laterality)


def make_timepoint(subject_id: str, timepoint_id: str | None = None, **kwargs: Any) -> Timepoint:
    return Timepoint(timepoint_id or _id("tp"), subject_id, **kwargs)


def make_acquisition(subject_id: str, timepoint_id: str, modality: str, source_type: str = "device", **kwargs: Any) -> Acquisition:
    return Acquisition(_id("acq"), subject_id, timepoint_id, source_type, modality, **kwargs)


def make_data_object(**kwargs: Any) -> DataObject:
    obj = DataObject(**kwargs)
    obj.validate()
    return obj
