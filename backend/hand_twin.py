from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .app import app
from .hand_analysis import ZONE_LANDMARKS, run_hand_analysis

TWIN_VERSION = "0.1"


def _region_contract(zone_id: str) -> dict[str, Any]:
    return {
        "id": zone_id,
        "landmark_indices": ZONE_LANDMARKS[zone_id],
        "observations": [],
        "roi": None,
        "deeper_evidence": {
            "tissue": [],
            "cellular": [],
            "molecular": [],
            "non_image": [],
        },
        "status": "unpopulated",
    }


def build_hand_twin() -> dict[str, Any]:
    analysis = run_hand_analysis()
    regions = {zone_id: _region_contract(zone_id) for zone_id in ZONE_LANDMARKS}

    for image in analysis.get("images", []):
        for hand in image.get("hands", []):
            for zone in hand.get("zones", []):
                region = regions.get(zone.get("id"))
                if region is None:
                    continue
                region["observations"].append({
                    "source_file": image.get("file"),
                    "hand_index": hand.get("index"),
                    "handedness": hand.get("handedness"),
                    "confidence": zone.get("confidence"),
                    "review_priority": zone.get("review_priority"),
                    "level": "macroscopic",
                    "provenance": "hand_analysis",
                })
                region["status"] = "observed"

    return {
        "twin_version": TWIN_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "subject": None,
        "session": None,
        "timepoint": None,
        "identity_status": "not_registered",
        "identity_rule": "Subject/session/timepoint must be explicitly registered; filenames do not establish identity.",
        "source": analysis.get("source", "own_cohort"),
        "representation": {
            "type": "landmark_based_hand_spatial_model",
            "coordinate_spaces": ["normalized_image_2d", "mediapipe_world_landmarks"],
            "physical_scale": "not_calibrated",
        },
        "anatomy": {
            "regions": list(regions.values()),
            "region_order": list(ZONE_LANDMARKS),
        },
        "observation_summary": {
            "files": analysis.get("files", 0),
            "images_with_hands": analysis.get("images_with_hands", 0),
            "hand_instances": analysis.get("hand_instances", 0),
            "zone_observations": len(analysis.get("zones", [])),
        },
        "evidence_boundary": {
            "available_now": ["macroscopic hand landmarks", "normalized geometry", "technical visibility", "source-image provenance"],
            "not_available": ["validated tissue state", "validated cellular state", "validated molecular state", "disease interpretation", "ageing interpretation"],
        },
        "next_measurement": "Register subject/session/timepoint, then attach repeat observations to the same region identifiers before longitudinal analysis.",
        "analysis_status": analysis.get("status"),
    }


@app.get("/api/hand/twin")
def hand_twin():
    return build_hand_twin()
