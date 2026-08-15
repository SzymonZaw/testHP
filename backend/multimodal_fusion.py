"""Explicit-link multimodal fusion for the Digital Biological Twin.

This module is intentionally conservative: it never creates a biological
relationship from filenames, dataset names, directory names or modality
similarity. A subject identifier is required; region linkage is required for
spatial fusion.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .multiscale_pipeline import DigitalTwinState, EvidenceRecord


def fuse_records(records: Iterable[EvidenceRecord], subject_id: str) -> dict:
    records = list(records)
    subject_records = [r for r in records if r.subject_id == subject_id]
    rejected = [
        {"source_id": r.source_id, "reason": "subject_mismatch_or_missing_explicit_link"}
        for r in records
        if r.subject_id != subject_id
    ]

    by_region: dict[str | None, list[dict]] = {}
    for record in subject_records:
        by_region.setdefault(record.region_id, []).append(asdict(record))

    return {
        "subject_id": subject_id,
        "status": "linked" if subject_records else "no_explicit_subject_evidence",
        "regions": [
            {"region_id": region, "evidence": evidence}
            for region, evidence in by_region.items()
        ],
        "rejected": rejected,
        "interpretation": "not established",
        "boundary": "fusion organizes evidence; it does not diagnose disease or infer biological age",
    }


def attach_to_twin(twin: DigitalTwinState, records: Iterable[EvidenceRecord], timepoint: str) -> None:
    """Attach already validated evidence to a twin snapshot."""
    records = list(records)
    twin.ensure_hand_zones()
    twin.add_timepoint(timepoint, records)
