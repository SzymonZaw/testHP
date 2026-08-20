"""Turn ingested raw assets into traceable, non-diagnostic observations."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from core.anatomy import AnatomicalLocation
from core.artifact import Artifact
from core.digital_twin_state import DigitalTwinState
from core.evidence import Evidence
from core.observation import Observation
from backend.anatomical_regions import map_anatomical_regions
from backend.hand_segmentation import detect_hand_landmarks
ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT / "data" / "registry" / "observations"
def _id(prefix: str) -> str: return f"{prefix}_{uuid.uuid4().hex[:12]}"
def _write_json(name: str, payload: Any) -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    (STATE_ROOT / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
def _anatomical_context(asset: dict[str, Any]) -> dict[str, Any]:
    if asset.get("modality") not in {"hand", "video"}:
        return {"region_id": asset.get("view") or asset.get("subtype") or "unassigned", "method": "metadata"}
    detection = detect_hand_landmarks(asset["path"])
    regions = map_anatomical_regions(detection.get("landmarks", []))
    if regions:
        primary = min(regions, key=lambda item: abs(item["centroid"]["x"] - 0.5) + abs(item["centroid"]["y"] - 0.5))
        return {"region_id": primary["region_id"], "method": "landmark-group", "detector": detection.get("method"), "landmarks": detection["landmarks"], "regions": regions}
    return {"region_id": asset.get("view") or asset.get("subtype") or "unassigned", "method": "metadata-fallback", "detector": detection.get("method"), "regions": []}
def register_asset(asset: dict[str, Any]) -> dict[str, Any]:
    subject_id, timepoint, modality = str(asset["subject_id"]), str(asset["timepoint"]), str(asset["modality"])
    context, region = _anatomical_context(asset), None
    region = str(context["region_id"])
    artifact = Artifact(id=asset.get("asset_id") or _id("artifact"), subject_id=subject_id, timepoint_id=timepoint, modality=modality, uri=str(asset["path"]), media_type=asset.get("media_type"), anatomical_location_id=f"hand/{region}" if modality in {"hand", "video"} else None, metadata={"source": asset.get("source", "raw"), "filename": asset.get("filename"), "size_bytes": asset.get("size_bytes", 0), "anatomical_mapping": context})
    location = AnatomicalLocation(id=f"hand/{region}", name=region, level="site", parent_id="hand")
    level = {"hand": "macro", "wsi": "tissue", "microscopy": "cellular", "cellular": "cellular", "rna": "molecular"}.get(modality, "unspecified")
    observation = Observation(id=_id("observation"), subject_id=subject_id, timepoint_id=timepoint, name="data_availability", value={"status": asset.get("status"), "modality": modality, "bytes": asset.get("size_bytes", 0)}, observed_at=datetime.now(timezone.utc), anatomical_location=location, metadata={"interpretation_boundary": "availability_only", "raw_path": asset["path"], "anatomical_mapping": context}, biological_level=level, modality=modality)
    evidence = Evidence(id=_id("evidence"), subject_id=subject_id, observation_id=observation.id, artifact_ids=[artifact.id], evidence_type="source_artifact", interpretation_boundary="observation_only", provenance={"path": asset["path"], "source": asset.get("source", "raw"), "anatomical_mapping": context}, confidence=1.0 if asset.get("status") == "available" else 0.0)
    twin = DigitalTwinState(subject_id=subject_id, entity_id="hand", entity_type="anatomical_fragment")
    twin.add_zone(region, name=region, parent_id="hand", priority="not_established"); twin.artifact_ids.append(artifact.id); twin.link_observation(observation.id, timepoint_id=timepoint, zone_id=region); twin.evidence_ids.append(evidence.id)
    twin.set_dimension("data_quality", {"status": asset.get("status"), "modality": modality}); twin.set_dimension("biological_inference", "not_established")
    result = {"artifact": artifact, "observation": observation, "evidence": evidence, "digital_twin": twin}; _write_json(f"{observation.id}.json", result); return result
def analyze_asset(asset: dict[str, Any]) -> dict[str, Any]:
    result = register_asset(asset)
    return {
        "status": "ready" if asset.get("status") == "available" else "warning",
        "analysis_level": "ingestion_quality",
        "biological_inference": "not_established",
        "asset_id": asset.get("asset_id") or result["artifact"].id,
        "subject_id": asset.get("subject_id"),
        "timepoint": asset.get("timepoint"),
        "modality": asset.get("modality"),
        "artifact": result["artifact"],
        "observation": result["observation"],
        "evidence": result["evidence"],
        "digital_twin": result["digital_twin"],
        "next_analysis": "macro_image_analysis" if asset.get("modality") in {"hand", "images"} else "modality_specific_analysis",
    }
