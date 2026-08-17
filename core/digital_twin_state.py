"""State model connecting longitudinal evidence to a digital twin."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DigitalTwinState:
    """Current, traceable state of one subject or anatomical fragment.

    This is a state container, not a diagnostic model. It can hold evidence
    from macro, micro, molecular, textual and numeric modalities and keep the
    mapping to anatomical regions explicit.
    """

    subject_id: str
    entity_id: str
    entity_type: str = "organism"
    zones: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    artifact_ids: list[str] = field(default_factory=list)
    observation_ids: list[str] = field(default_factory=list)
    measurement_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    state_dimensions: Dict[str, Any] = field(default_factory=dict)
    history: list[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.entity_id.strip():
            raise ValueError("DigitalTwinState subject_id and entity_id cannot be empty")

    def add_zone(self, zone_id: str, *, name: str, parent_id: str | None = None, priority: str = "not_established") -> None:
        if not zone_id.strip():
            raise ValueError("zone_id cannot be empty")
        self.zones[zone_id] = {"id": zone_id, "name": name, "parent_id": parent_id, "priority": priority}

    def link_observation(self, observation_id: str, *, timepoint_id: str, zone_id: str | None = None) -> None:
        self.observation_ids.append(observation_id)
        self.history.append({"timepoint_id": timepoint_id, "observation_id": observation_id, "zone_id": zone_id})

    def set_dimension(self, name: str, value: Any) -> None:
        """Set a state dimension such as ageing, damage, inflammation or pathology risk."""
        if not name.strip():
            raise ValueError("state dimension name cannot be empty")
        self.state_dimensions[name] = value
