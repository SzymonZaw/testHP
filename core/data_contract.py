"""Canonical user-input validation and mapping for the digital-twin pipeline.

This module deliberately does not read the repository's raw data directory. It
validates a caller-provided submission and maps declared artifacts to the
existing Measurement -> Observation -> Evidence domain model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Iterable

from .anatomy import AnatomicalLocation
from .biomarker import Biomarker
from .evidence import Evidence
from .measurement import Measurement
from .observation import Observation


ALLOWED_HAND_SIDES = {"left", "right", "bilateral", "unknown"}
ALLOWED_VIEWS = {"dorsal", "palmar", "thumb", "lateral", "oblique", "unknown"}
LEVELS = ("macro", "tissue", "cellular", "molecular")


@dataclass(frozen=True)
class IngestBundle:
    """Domain objects created from one contract submission."""

    measurements: list[Measurement]
    observations: list[Observation]
    evidence: list[Evidence]
    missing_levels: list[str]


def validate_submission(submission: dict[str, Any]) -> list[str]:
    """Return validation errors; an empty list means the contract is valid."""
    errors: list[str] = []
    if not isinstance(submission, dict):
        return ["submission must be an object"]
    subject_id = submission.get("subject_id")
    if not isinstance(subject_id, str) or not subject_id.strip():
        errors.append("subject_id is required")

    timepoints = submission.get("timepoints")
    if not isinstance(timepoints, list) or not timepoints:
        errors.append("timepoints must contain at least one timepoint")
        return errors

    for i, tp in enumerate(timepoints):
        prefix = f"timepoints[{i}]"
        if not isinstance(tp, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(tp.get("timepoint_id"), str) or not tp["timepoint_id"].strip():
            errors.append(f"{prefix}.timepoint_id is required")
        acquisition = tp.get("acquisition_time")
        if not isinstance(acquisition, str) or not acquisition.strip():
            errors.append(f"{prefix}.acquisition_time is required")
        else:
            try:
                datetime.fromisoformat(acquisition.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{prefix}.acquisition_time must be ISO-8601")

        age = tp.get("chronological_age_years", submission.get("metadata", {}).get("chronological_age_years"))
        if age is not None and (not isinstance(age, (int, float)) or age < 0 or age > 130):
            errors.append(f"{prefix}.chronological_age_years must be between 0 and 130")

        hands = tp.get("hand_observations")
        if not isinstance(hands, list) or not hands:
            errors.append(f"{prefix}.hand_observations must contain at least one observation")
            continue
        for j, hand in enumerate(hands):
            hp = f"{prefix}.hand_observations[{j}]"
            if not isinstance(hand, dict):
                errors.append(f"{hp} must be an object")
                continue
            if hand.get("hand_side") not in ALLOWED_HAND_SIDES:
                errors.append(f"{hp}.hand_side is invalid")
            if hand.get("view") not in ALLOWED_VIEWS:
                errors.append(f"{hp}.view is invalid")
            file_obj = hand.get("file")
            if not isinstance(file_obj, dict) or not isinstance(file_obj.get("path"), str) or not file_obj["path"].strip():
                errors.append(f"{hp}.file.path is required")
            elif not isinstance(file_obj.get("modality"), str) or not file_obj["modality"].strip():
                errors.append(f"{hp}.file.modality is required")

        for key in ("tissue_samples", "cellular_samples", "molecular_samples"):
            samples = tp.get(key, [])
            if not isinstance(samples, list):
                errors.append(f"{prefix}.{key} must be an array")
                continue
            for j, artifact in enumerate(samples):
                if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("modality"):
                    errors.append(f"{prefix}.{key}[{j}] requires path and modality")
    return errors


def _artifact_id(path: str) -> str:
    return "artifact:" + str(PurePosixPath(path))


def _location_for_hand(hand: dict[str, Any]) -> AnatomicalLocation:
    side = hand["hand_side"]
    return AnatomicalLocation(
        id=f"hand:{side}",
        name=f"{side} hand",
        level="site",
    )


def _level_for_modality(modality: str) -> str:
    value = modality.lower()
    if any(x in value for x in ("rna", "transcript", "genomic", "proteom", "metabol")):
        return "molecular"
    if any(x in value for x in ("single_cell", "scRNA", "cell", "microscop")):
        return "cellular"
    if any(x in value for x in ("wsi", "histology", "tissue")):
        return "tissue"
    return "macro"


def build_ingest_bundle(submission: dict[str, Any]) -> IngestBundle:
    """Validate and convert a user submission into existing domain objects."""
    errors = validate_submission(submission)
    if errors:
        raise ValueError("Invalid data contract: " + "; ".join(errors))

    subject_id = submission["subject_id"]
    measurements: list[Measurement] = []
    observations: list[Observation] = []
    evidence: list[Evidence] = []
    observed_levels: set[str] = set()

    for tp in submission["timepoints"]:
        observed_at = datetime.fromisoformat(tp["acquisition_time"].replace("Z", "+00:00"))
        tp_id = tp["timepoint_id"]
        artifacts: list[tuple[dict[str, Any], AnatomicalLocation | None]] = []
        for hand in tp["hand_observations"]:
            artifacts.append((hand["file"], _location_for_hand(hand)))
        for key in ("tissue_samples", "cellular_samples", "molecular_samples"):
            artifacts.extend((a, None) for a in tp.get(key, []))

        for index, (artifact, location) in enumerate(artifacts):
            path = artifact["path"]
            modality = artifact["modality"]
            level = _level_for_modality(modality)
            observed_levels.add(level)
            artifact_id = _artifact_id(path)
            measurement_id = f"measurement:{tp_id}:{index}"
            observation_id = f"observation:{tp_id}:{index}"
            evidence_id = f"evidence:{tp_id}:{index}"
            biomarker = Biomarker(
                id=f"artifact:{modality}",
                name=f"{modality} artifact",
                category=level,
            )
            measurement = Measurement(
                id=measurement_id,
                subject_id=subject_id,
                timepoint_id=tp_id,
                modality=modality,
                biomarker=biomarker,
                value={"artifact_id": artifact_id, "path": path},
                measured_at=observed_at,
                anatomical_location=location,
                source="user_submission",
            )
            observation = Observation(
                id=observation_id,
                subject_id=subject_id,
                timepoint_id=tp_id,
                name=f"user artifact: {modality}",
                value={"artifact_id": artifact_id, "path": path},
                observed_at=observed_at,
                anatomical_location=location,
                source_measurement_ids=[measurement_id],
                biological_level=level,
                modality=modality,
                metadata={"evidence_status": "observed", "source": "user_submission"},
            )
            ev = Evidence(
                id=evidence_id,
                subject_id=subject_id,
                observation_id=observation_id,
                artifact_ids=[artifact_id],
                measurement_ids=[measurement_id],
                evidence_type="user_input",
                interpretation_boundary="artifact_observed_only",
                provenance={"source": "user_submission", "path": path},
            )
            measurements.append(measurement)
            observations.append(observation)
            evidence.append(ev)

    return IngestBundle(
        measurements=measurements,
        observations=observations,
        evidence=evidence,
        missing_levels=[level for level in LEVELS if level not in observed_levels],
    )
