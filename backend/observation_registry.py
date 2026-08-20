"""Persistent CRUD registry for explicit biological observations."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.anatomy import AnatomicalLocation
from core.observation import Observation

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = ROOT / "data" / "registry" / "manual_observations"
LEVELS = {"macro", "tissue", "cellular", "molecular"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"observation_{uuid.uuid4().hex[:12]}"


def _path(observation_id: str) -> Path:
    safe = "".join(ch for ch in observation_id if ch.isalnum() or ch in "-_")
    if not safe or safe != observation_id:
        raise ValueError("Invalid observation id")
    return REGISTRY_ROOT / f"{safe}.json"


def _location(payload: dict[str, Any]) -> AnatomicalLocation:
    spatial_id = str(payload.get("spatial_id") or "hand")
    return AnatomicalLocation(id=spatial_id, name=str(payload.get("location_name") or spatial_id.rsplit("/", 1)[-1]), level=str(payload.get("location_level") or "site"), parent_id=payload.get("parent_id"))


def _domain(payload: dict[str, Any], *, observation_id: str, version: int, created_at: str, updated_at: str) -> Observation:
    return Observation(id=observation_id, subject_id=str(payload["subject_id"]), timepoint_id=str(payload["timepoint"]), name=str(payload["name"]), value=payload.get("value"), observed_at=datetime.fromisoformat(str(payload["observed_at"]).replace("Z", "+00:00")), anatomical_location=_location(payload), source_measurement_ids=list(payload.get("source_measurement_ids") or []), metadata={"biological_level": payload["biological_level"], "modality": payload["modality"], "source": payload.get("source") or "manual-entry", "notes": payload.get("notes") or "", "evidence_id": payload.get("evidence_id"), "evidence_confidence": payload.get("evidence_confidence"), "evidence_type": payload.get("evidence_type") or "source", "validated_interpretations": payload.get("validated_interpretations") or {}, "version": version, "created_at": created_at, "updated_at": updated_at, "audit": payload.get("audit") or []})


def _serialize(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item)


def list_observations(*, subject_id: str, timepoint: str | None = None, spatial_id: str | None = None, biological_level: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
    REGISTRY_ROOT.mkdir(parents=True, exist_ok=True)
    result: list[dict[str, Any]] = []
    for path in sorted(REGISTRY_ROOT.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("subject_id") != subject_id: continue
        if timepoint and item.get("timepoint") != timepoint: continue
        if spatial_id and item.get("spatial_id") != spatial_id: continue
        if biological_level and item.get("biological_level") != biological_level: continue
        if not include_archived and item.get("status") == "archived": continue
        result.append(_serialize(item))
    return result


def get_observation(observation_id: str) -> dict[str, Any] | None:
    path = _path(observation_id)
    if not path.exists(): return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write(item: dict[str, Any]) -> None:
    REGISTRY_ROOT.mkdir(parents=True, exist_ok=True)
    _path(str(item["id"])).write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")


def create_observation(payload: dict[str, Any]) -> dict[str, Any]:
    level = str(payload.get("biological_level") or "").lower()
    if level not in LEVELS: raise ValueError(f"biological_level must be one of: {', '.join(sorted(LEVELS))}")
    name = str(payload.get("name") or "").strip(); subject_id = str(payload.get("subject_id") or "").strip(); timepoint = str(payload.get("timepoint") or "").strip(); spatial_id = str(payload.get("spatial_id") or "").strip()
    if not subject_id or not timepoint or not spatial_id or not name: raise ValueError("subject_id, timepoint, spatial_id and name are required")
    observation_id = _new_id(); now = _now(); author = str(payload.get("author") or "local-user").strip() or "local-user"
    item = {"id": observation_id, "subject_id": subject_id, "timepoint": timepoint, "spatial_id": spatial_id, "location_name": payload.get("location_name") or spatial_id.rsplit("/", 1)[-1], "location_level": payload.get("location_level") or "site", "parent_id": payload.get("parent_id"), "biological_level": level, "modality": str(payload.get("modality") or "manual-entry"), "name": name, "value": payload.get("value"), "observed_at": payload.get("observed_at") or now, "source": str(payload.get("source") or "manual-entry").strip(), "notes": str(payload.get("notes") or "").strip(), "evidence_id": payload.get("evidence_id"), "evidence_confidence": payload.get("evidence_confidence"), "evidence_type": payload.get("evidence_type") or "source", "validated_interpretations": payload.get("validated_interpretations") or {}, "author": author, "source_measurement_ids": list(payload.get("source_measurement_ids") or []), "status": "active", "version": 1, "created_at": now, "updated_at": now, "audit": [{"version": 1, "action": "created", "at": now, "author": author, "source": str(payload.get("source") or "manual-entry")}]}
    _domain(item, observation_id=observation_id, version=1, created_at=now, updated_at=now); _write(item)
    return item


def update_observation(observation_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    item = get_observation(observation_id)
    if item is None: return None
    if "biological_level" in patch:
        level = str(patch["biological_level"]).lower()
        if level not in LEVELS: raise ValueError(f"biological_level must be one of: {', '.join(sorted(LEVELS))}")
    if "evidence_confidence" in patch and patch["evidence_confidence"] is not None and not 0.0 <= float(patch["evidence_confidence"]) <= 1.0:
        raise ValueError("evidence_confidence must be between 0 and 1")
    allowed = {"name", "value", "observed_at", "source", "notes", "modality", "biological_level", "evidence_id", "evidence_confidence", "evidence_type", "validated_interpretations", "source_measurement_ids"}
    changes = {key: value for key, value in patch.items() if key in allowed}
    if not changes: return item
    now = _now(); previous_version = int(item.get("version") or 1); author = str(patch.get("author") or item.get("author") or "local-user").strip() or "local-user"
    diff = {key: {"before": item.get(key), "after": value} for key, value in changes.items()}
    item.update(changes); item["author"] = author; item["version"] = previous_version + 1; item["updated_at"] = now
    item.setdefault("audit", []).append({"version": item["version"], "action": "updated", "at": now, "author": author, "changed_fields": sorted(changes), "diff": diff}); _domain(item, observation_id=observation_id, version=item["version"], created_at=item.get("created_at", now), updated_at=now); _write(item)
    return item


def archive_observation(observation_id: str, *, author: str = "local-user", reason: str = "") -> dict[str, Any] | None:
    item = get_observation(observation_id)
    if item is None: return None
    if item.get("status") == "archived": return item
    now = _now(); item["status"] = "archived"; item["updated_at"] = now; item.setdefault("audit", []).append({"version": int(item.get("version") or 1), "action": "archived", "at": now, "author": author, "reason": reason}); _write(item)
    return item


def restore_observation(observation_id: str, *, author: str = "local-user", reason: str = "") -> dict[str, Any] | None:
    item = get_observation(observation_id)
    if item is None: return None
    if item.get("status") != "archived": return item
    now = _now(); item["status"] = "active"; item["updated_at"] = now; item.setdefault("audit", []).append({"version": int(item.get("version") or 1), "action": "restored", "at": now, "author": author, "reason": reason}); _write(item)
    return item


def observation_history(observation_id: str) -> list[dict[str, Any]] | None:
    item = get_observation(observation_id)
    return None if item is None else list(item.get("audit") or [])
