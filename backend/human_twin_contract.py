from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganTwinRef:
    organ_id: str
    organ_type: str
    local_twin_id: str


@dataclass(frozen=True)
class CrossOrganRelation:
    relation_id: str
    source_organ_id: str
    target_organ_id: str
    relation_type: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = None


@dataclass(frozen=True)
class SystemicRiskEntry:
    target_id: str
    risk_level: str
    score: float | None = None
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class HumanDigitalTwin:
    human_id: str
    organ_twins: tuple[OrganTwinRef, ...]
    cross_organ_relations: tuple[CrossOrganRelation, ...] = ()
    systemic_risks: tuple[SystemicRiskEntry, ...] = ()
    history_timepoint_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        organ_ids = [item.organ_id for item in self.organ_twins]
        if len(organ_ids) != len(set(organ_ids)):
            raise ValueError("organ IDs must be unique")
        known = set(organ_ids)
        for relation in self.cross_organ_relations:
            if relation.source_organ_id not in known or relation.target_organ_id not in known:
                raise ValueError("cross-organ relation references unknown organ")
            if relation.confidence is not None and not 0 <= relation.confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")
