from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ZoneHistory:
    observations_by_timepoint: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def add(self, timepoint: str, observation: dict[str, Any]) -> None:
        self.observations_by_timepoint.setdefault(timepoint, []).append(observation)


@dataclass
class HandZone:
    zone_id: str
    name: str
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    history: ZoneHistory = field(default_factory=ZoneHistory)


@dataclass
class HandTwin:
    hand_id: str
    laterality: str
    zones: dict[str, HandZone] = field(default_factory=dict)


@dataclass
class PersonTwin:
    person_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    hands: dict[str, HandTwin] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def ensure_hand(self, hand_id: str = "hand-1", laterality: str = "unknown") -> HandTwin:
        if hand_id not in self.hands:
            self.hands[hand_id] = HandTwin(hand_id=hand_id, laterality=laterality)
        return self.hands[hand_id]

    def add_zone(self, hand_id: str, zone_id: str, name: str, parent_id: str | None = None, children: list[str] | None = None, laterality: str = "unknown") -> HandZone:
        hand = self.ensure_hand(hand_id, laterality)
        zone = hand.zones.get(zone_id)
        if zone is None:
            zone = HandZone(zone_id=zone_id, name=name, parent_id=parent_id, children=list(children or []))
            hand.zones[zone_id] = zone
        else:
            zone.name = name
            zone.parent_id = parent_id
            if children is not None:
                zone.children = list(children)
        return zone

    def add_observation(self, hand_id: str, zone_id: str, timepoint: str, observation: dict[str, Any], laterality: str = "unknown") -> None:
        hand = self.ensure_hand(hand_id, laterality)
        if zone_id not in hand.zones:
            hand.zones[zone_id] = HandZone(zone_id=zone_id, name=zone_id)
        hand.zones[zone_id].history.add(timepoint, observation)

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


def build_twin(person_id: str, ontology: dict[str, Any], metadata: dict[str, Any] | None = None) -> PersonTwin:
    twin = PersonTwin(person_id=person_id, metadata=dict(metadata or {}))
    for region in ontology.get("hand", []):
        region_id = region["id"]
        children = list(region.get("children") or [])
        twin.add_zone("hand-1", region_id, region.get("name", region_id), children=children)
        for child in children:
            child_id = f"{region_id}.{child}"
            twin.add_zone("hand-1", child_id, child, parent_id=region_id)
    return twin
