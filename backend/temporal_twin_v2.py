from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Timepoint:
    timepoint_id: str
    observed_at: str
    study_id: str | None = None
    label: str | None = None

@dataclass(frozen=True)
class TemporalObservation:
    observation_id: str
    spatial_id: str
    timepoint_id: str
    features: dict[str,float] = field(default_factory=dict)

@dataclass(frozen=True)
class TemporalChange:
    change_id: str
    spatial_id: str
    from_timepoint: str
    to_timepoint: str
    deltas: dict[str,float] = field(default_factory=dict)
    rate_per_year: dict[str,float] = field(default_factory=dict)
    direction: str = "unknown"
    confidence: float | None = None
    evidence_ids: tuple[str,...] = ()
    def validate(self)->None:
        if self.confidence is not None and not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")

@dataclass(frozen=True)
class TemporalTwin:
    twin_id: str
    timepoints: tuple[Timepoint,...] = ()
    observations: tuple[TemporalObservation,...] = ()
    changes: tuple[TemporalChange,...] = ()
    def validate(self)->None:
        ids={t.timepoint_id for t in self.timepoints}
        if len(ids)!=len(self.timepoints): raise ValueError("timepoint IDs must be unique")
        for c in self.changes:
            c.validate()
            if c.from_timepoint not in ids or c.to_timepoint not in ids: raise ValueError("unknown timepoint")
