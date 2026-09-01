from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RegistrationStatus(str, Enum):
    UNREGISTERED = "unregistered"
    CANDIDATE = "candidate"
    VERIFIED = "verified"


@dataclass(frozen=True)
class SpatialTransform:
    """Explicit sample-local -> canonical-hand transform metadata.

    The transform is intentionally optional: a missing transform means that
    sample-local coordinates must not be displayed as if they were hand-space
    coordinates.
    """

    transform_id: str
    source_frame: str
    target_frame: str
    matrix: tuple[tuple[float, float, float], ...]
    method: str
    status: RegistrationStatus = RegistrationStatus.CANDIDATE
    evidence_ids: tuple[str, ...] = ()
    model_version: str | None = None

    def validate(self) -> None:
        if not self.transform_id:
            raise ValueError("transform_id is required")
        if not self.source_frame or not self.target_frame:
            raise ValueError("source_frame and target_frame are required")
        if len(self.matrix) != 3 or any(len(row) != 3 for row in self.matrix):
            raise ValueError("matrix must be 3x3")
        if not self.method:
            raise ValueError("registration method is required")
        if self.status is RegistrationStatus.VERIFIED and not self.evidence_ids:
            raise ValueError("verified registration requires evidence_ids")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "transform_id": self.transform_id,
            "source_frame": self.source_frame,
            "target_frame": self.target_frame,
            "matrix": [list(row) for row in self.matrix],
            "method": self.method,
            "status": self.status.value,
            "evidence_ids": list(self.evidence_ids),
            "model_version": self.model_version,
        }


@dataclass(frozen=True)
class RegistrationAssessment:
    source_id: str
    source_region: str
    target_region: str
    status: RegistrationStatus
    transform: SpatialTransform | None = None
    anatomical_match: bool = False
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_id or not self.source_region or not self.target_region:
            raise ValueError("source and target region identity is required")
        if self.status is RegistrationStatus.VERIFIED:
            if not self.anatomical_match:
                raise ValueError("verified registration requires anatomical_match")
            if self.transform is None:
                raise ValueError("verified registration requires a transform")
            self.transform.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "source_id": self.source_id,
            "source_region": self.source_region,
            "target_region": self.target_region,
            "status": self.status.value,
            "transform": self.transform.to_dict() if self.transform else None,
            "anatomical_match": self.anatomical_match,
            "limitations": list(self.limitations),
        }
