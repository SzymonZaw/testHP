"""Adapters from the existing hand evidence pipeline to the core domain model."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core import AnatomicalLocation, Artifact, Biomarker, Measurement, Observation
from backend.multiscale_pipeline import EvidenceRecord


def _location(region_id: str | None) -> AnatomicalLocation | None:
    if not region_id:
        return None
    return AnatomicalLocation(region_id, region_id.replace(".", " / "), "site")


def evidence_to_artifacts(records: Iterable[EvidenceRecord], timepoint_id: str) -> list[Artifact]:
    """Create one source artifact per unique evidence source."""
    artifacts: list[Artifact] = []
    seen: set[tuple[str | None, str]] = set()
    for index, record in enumerate(records, start=1):
        key = (record.subject_id, record.source_id)
        if key in seen:
            continue
        seen.add(key)
        artifacts.append(
            Artifact(
                id=f"ART-HAND-{index:05d}",
                subject_id=record.subject_id or "unknown",
                timepoint_id=timepoint_id,
                modality=record.modality,
                uri=record.source_id,
                anatomical_location_id=record.region_id,
                metadata={"biological_level": record.biological_level, "provenance": record.provenance},
            )
        )
    return artifacts


def evidence_to_measurements(records: Iterable[EvidenceRecord], timepoint_id: str) -> list[Measurement]:
    """Represent numeric evidence as Measurements while preserving source provenance."""
    measurements: list[Measurement] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record.value, (int, float)) or isinstance(record.value, bool):
            continue
        biomarker = Biomarker(
            id=f"{record.modality}:{record.metric}",
            name=record.metric,
            category=record.biological_level,
            unit=record.unit,
        )
        measurements.append(
            Measurement(
                id=f"MEAS-HAND-{index:05d}",
                subject_id=record.subject_id or "unknown",
                timepoint_id=timepoint_id,
                modality=record.modality,
                biomarker=biomarker,
                value=record.value,
                measured_at=datetime.now(timezone.utc),
                anatomical_location=_location(record.region_id),
                unit=record.unit,
                source=record.source_id,
                processing_version=str(record.provenance.get("pipeline_version", "unknown")),
            )
        )
    return measurements


def evidence_to_observations(records: Iterable[EvidenceRecord], timepoint_id: str) -> list[Observation]:
    """Represent pipeline records as observations without adding diagnostic meaning."""
    observations: list[Observation] = []
    for index, record in enumerate(records, start=1):
        observations.append(
            Observation(
                id=f"OBS-HAND-{index:05d}",
                subject_id=record.subject_id or "unknown",
                timepoint_id=timepoint_id,
                name=record.metric,
                value=record.value,
                observed_at=datetime.now(timezone.utc),
                anatomical_location=_location(record.region_id),
                metadata={
                    "modality": record.modality,
                    "biological_level": record.biological_level,
                    "result_type": record.result_type,
                    "status": record.status,
                    "uncertainty": record.uncertainty,
                    "provenance": record.provenance,
                },
            )
        )
    return observations
