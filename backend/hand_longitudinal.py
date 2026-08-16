from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

HAND_ZONES = (
    "wrist", "palm", "thumb", "index", "middle", "ring", "little",
    "nails", "skin_regions",
)

OBSERVATION_TYPES = (
    "geometry", "landmark_quality", "image_quality", "appearance", "motion",
    "depth", "microstructure", "cellular", "molecular",
)

@dataclass(frozen=True)
class SubjectRef:
    subject_id: str
    session_id: str
    timepoint: str

@dataclass
class HandObservation:
    subject_id: str
    session_id: str
    timepoint: str
    hand_id: str
    laterality: str
    zone: str
    observation_type: str
    metric: str
    value: float | int | str | None
    unit: str | None = None
    source_file: str | None = None
    confidence: float | None = None
    evidence_level: str = "observed"
    notes: str | None = None

    def validate(self) -> None:
        if not self.subject_id.strip(): raise ValueError("subject_id is required")
        if not self.session_id.strip(): raise ValueError("session_id is required")
        if not self.timepoint.strip(): raise ValueError("timepoint is required")
        if self.laterality not in {"left", "right", "unknown"}:
            raise ValueError("laterality must be left, right or unknown")
        if self.zone not in HAND_ZONES: raise ValueError(f"unknown hand zone: {self.zone}")
        if self.observation_type not in OBSERVATION_TYPES:
            raise ValueError(f"unknown observation type: {self.observation_type}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.evidence_level != "observed":
            raise ValueError("hand observations must remain observed; interpretation is a separate layer")

    def to_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)

@dataclass
class HandTimepoint:
    ref: SubjectRef
    hand_ids: list[str] = field(default_factory=list)
    observations: list[HandObservation] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add(self, observation: HandObservation) -> None:
        if observation.subject_id != self.ref.subject_id: raise ValueError("observation subject_id does not match timepoint")
        if observation.session_id != self.ref.session_id: raise ValueError("observation session_id does not match timepoint")
        if observation.timepoint != self.ref.timepoint: raise ValueError("observation timepoint does not match timepoint record")
        observation.validate()
        if observation.hand_id not in self.hand_ids: self.hand_ids.append(observation.hand_id)
        self.observations.append(observation)

    def to_dict(self) -> dict[str, Any]:
        return {"subject": asdict(self.ref), "hand_ids": list(self.hand_ids), "observations": [x.to_dict() for x in self.observations], "created_at": self.created_at}

def make_observation(**kwargs: Any) -> HandObservation:
    observation = HandObservation(**kwargs); observation.validate(); return observation

def compare_numeric_observations(baseline: list[HandObservation], current: list[HandObservation]) -> list[dict[str, Any]]:
    base_map = {(x.hand_id, x.zone, x.metric): x.value for x in baseline if isinstance(x.value, (int, float))}
    changes = []
    for obs in current:
        key = (obs.hand_id, obs.zone, obs.metric)
        if key not in base_map or not isinstance(obs.value, (int, float)): continue
        old, new = float(base_map[key]), float(obs.value); delta = new - old
        changes.append({"hand_id": obs.hand_id, "zone": obs.zone, "metric": obs.metric, "baseline": old, "current": new, "delta": delta, "relative_change": None if old == 0 else delta / abs(old), "evidence_level": "observed_change", "interpretation": None})
    return changes

def rank_zones_by_change(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    for change in changes:
        value = change.get("relative_change")
        if isinstance(value, (int, float)): scores[change["zone"]] = scores.get(change["zone"], 0.0) + abs(float(value))
    return [{"zone": zone, "change_score": round(score, 6), "reason": "largest measured change relative to baseline", "interpretation": None} for zone, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)]

def build_hand_snapshot(subject_id: str, session_id: str, timepoint: str, observations: list[HandObservation]) -> dict[str, Any]:
    record = HandTimepoint(SubjectRef(subject_id, session_id, timepoint))
    for observation in observations: record.add(observation)
    zones = {zone: [] for zone in HAND_ZONES}
    for observation in record.observations: zones[observation.zone].append(observation.to_dict())
    return {"subject": asdict(record.ref), "hand_ids": record.hand_ids, "zones": zones, "observation_count": len(record.observations), "evidence_boundary": "observations only; no diagnosis or biological conclusion"}
