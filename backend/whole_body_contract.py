from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrganTwinRef:
    organ_id: str
    organ_type: str
    spatial_root_id: str | None = None


@dataclass(frozen=True)
class CrossOrganRelation:
    relation_id: str
    source_organ_id: str
    target_organ_id: str
    relation_type: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class HumanDigitalTwin:
    human_id: str
    organs: tuple[OrganTwinRef, ...] = ()
    relations: tuple[CrossOrganRelation, ...] = ()
    systemic_risk_ids: tuple[str, ...] = ()
    timepoint_ids: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.human_id:
            raise ValueError("human digital twin identity is required")
        organ_ids = {organ.organ_id for organ in self.organs}
        for relation in self.relations:
            if relation.source_organ_id not in organ_ids or relation.target_organ_id not in organ_ids:
                raise ValueError("cross-organ relation references an unknown organ")
