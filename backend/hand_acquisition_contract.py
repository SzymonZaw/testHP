"""Canonical acquisition identifiers for hand observations.

This module is deliberately small: it gives every captured artifact a stable
subject/session/timepoint identity without interpreting biological state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class HandAcquisition:
    subject_id: str
    session_id: str
    timepoint_id: str
    modality: str
    source_role: str = "own_cohort"
    captured_at: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("subject_id", "session_id", "timepoint_id", "modality"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")
        if self.source_role not in {"own_cohort", "reference"}:
            raise ValueError("source_role must be own_cohort or reference")

    @property
    def acquisition_id(self) -> str:
        raw = ":".join((self.subject_id, self.session_id, self.timepoint_id, self.modality))
        return "ACQ-HAND-" + sha256(raw.encode("utf-8")).hexdigest()[:16]


def infer_session_id(root: str | Path, subject_id: str, timepoint_id: str) -> str:
    """Return a deterministic session id for a capture directory."""
    path = Path(root).resolve()
    raw = f"{subject_id}:{timepoint_id}:{path.as_posix()}"
    return "SES-HAND-" + sha256(raw.encode("utf-8")).hexdigest()[:16]
