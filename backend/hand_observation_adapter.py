"""Adapters from hand evidence into the core domain model."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from core import AnatomicalLocation, Artifact, Biomarker, Measurement, Observation
from backend.hand_acquisition_contract import HandAcquisition, infer_session_id
from backend.multiscale_pipeline import EvidenceRecord


def _location(region_id: str | None) -> AnatomicalLocation | None:
    if not region_id:
        return None
    return AnatomicalLocation(region_id, region_id.replace(".", " / "), "site")


def acquisition_for_record(record: EvidenceRecord, *, session_id: str | None = None) -> HandAcquisition:
    """Build canonical acquisition identity from an evidence record."""
    timepoint = str(record.provenance.get("timepoint", "T0"))
    subject = record.subject_id or "unknown"
    session = session_id or str(record.provenance.get("session_id", ""))
    if not session:
        session = infer_session_id(".", subject, timepoint)
    source_role = str(record.provenance.get("source_role", "own_cohort"))
    captured_at = record.provenance.get("captured_at")
    if isinstance(captured_at, str):
        try:
            captured_at = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError:
            captured_at = None
    return HandAcquisition(subject, session, timepoint, record.modality, source_role, captured_at, dict(record.provenance))


def evidence_to_artifacts(records: Iterable[EvidenceRecord], timepoint_id: str, session_id: str | None = None) -> list[Artifact]:
    """Create one source artifact per unique acquisition/source pair."""
    artifacts: list[Artifact] = []
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(records, start=1):
        acquisition = acquisition_for_record(record, session_id=session_id)
        key = (acquisition.acquisition_id, record.source_id)
        if key in seen:
            continue
        seen.add(key)
        artifacts.append(Artifact(
            id=f"ART-HAND-{index:05d}", subject_id=acquisition.subject_id,
            timepoint_id=acquisition.timepoint_id or timepoint_id, modality=record.modality,
            uri=record.source_id, anatomical_location_id=record.region_id,
            metadata={"acquisition_id": acquisition.acquisition_id, "session_id": acquisition.session_id,
                      "source_role": acquisition.source_role, "biological_level": record.biological_level,
                      "provenance": record.provenance},
        ))
    return artifacts


def evidence_to_measurements(records: Iterable[EvidenceRecord], timepoint_id: str, session_id: str | None = None) -> list[Measurement]:
    """Represent numeric evidence as Measurements with acquisition provenance."""
    measurements: list[Measurement] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record.value, (int, float)) or isinstance(record.value, bool):
            continue
        acquisition = acquisition_for_record(record, session_id=session_id)
        biomarker = Biomarker(id=f"{record.modality}:{record.metric}", name=record.metric,
                              category=record.biological_level, unit=record.unit)
        measurements.append(Measurement(
            id=f"MEAS-HAND-{index:05d}", subject_id=acquisition.subject_id,
            timepoint_id=acquisition.timepoint_id or timepoint_id, modality=record.modality,
            biomarker=biomarker, value=record.value, measured_at=acquisition.captured_at or datetime.now(timezone.utc),
            anatomical_location=_location(record.region_id), unit=record.unit, source=record.source_id,
            processing_version=str(record.provenance.get("pipeline_version", "unknown")),
        ))
    return measurements


def evidence_to_observations(records: Iterable[EvidenceRecord], timepoint_id: str, session_id: str | None = None) -> list[Observation]:
    """Represent records as observations while retaining canonical acquisition identity."""
    observations: list[Observation] = []
    for index, record in enumerate(records, start=1):
        acquisition = acquisition_for_record(record, session_id=session_id)
        observations.append(Observation(
            id=f"OBS-HAND-{index:05d}", subject_id=acquisition.subject_id,
            timepoint_id=acquisition.timepoint_id or timepoint_id, name=record.metric, value=record.value,
            observed_at=acquisition.captured_at or datetime.now(timezone.utc), anatomical_location=_location(record.region_id),
            metadata={"modality": record.modality, "biological_level": record.biological_level,
                      "result_type": record.result_type, "status": record.status, "uncertainty": record.uncertainty,
                      "acquisition_id": acquisition.acquisition_id, "session_id": acquisition.session_id,
                      "source_role": acquisition.source_role, "provenance": record.provenance},
        ))
    return observations
