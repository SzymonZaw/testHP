"""Canonical validation state for user-submitted multimodal input packages.

This module validates the v1 user-input contract without reading local raw data.
It intentionally distinguishes availability from scientific interpretation:
missing modalities remain unavailable and are never fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Any


class ModalityStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    INVALID = "invalid"
    MISSING = "missing"


class EvidenceStatus(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    PREDICTED = "predicted"
    GROUND_TRUTH = "ground_truth"
    UNAVAILABLE = "unavailable"


MODALITIES = (
    "hand_images", "hand_video", "hand_3d", "tissue_wsi", "microscopy",
    "single_cell_rna", "bulk_rna", "genomics", "proteomics", "epigenetics",
    "clinical_context", "ground_truth",
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class ModalityReport:
    modality: str
    status: ModalityStatus
    input_ids: tuple[str, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True)
class InputValidationReport:
    valid: bool
    subject_id: str | None
    timepoint_ids: tuple[str, ...]
    modalities: dict[str, ModalityReport]
    evidence_status: EvidenceStatus
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def available_modalities(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.modalities.items() if v.status == ModalityStatus.AVAILABLE)

    @property
    def missing_modalities(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.modalities.items() if v.status == ModalityStatus.MISSING)


def _issue(path: str, message: str) -> ValidationIssue:
    return ValidationIssue(path, message)


def _is_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _validate_input(item: Any, index: int) -> list[ValidationIssue]:
    path = f"inputs[{index}]"
    issues: list[ValidationIssue] = []
    if not isinstance(item, dict):
        return [_issue(path, "must be an object")]
    for key in ("input_id", "kind", "uri", "format", "provenance"):
        if key not in item:
            issues.append(_issue(f"{path}.{key}", "is required"))
    if item.get("kind") not in MODALITIES:
        issues.append(_issue(f"{path}.kind", "is not a supported modality"))
    for key in ("input_id", "uri", "format"):
        if key in item and (not isinstance(item[key], str) or not item[key].strip()):
            issues.append(_issue(f"{path}.{key}", "must be a non-empty string"))
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        issues.append(_issue(f"{path}.provenance", "must be an object"))
    elif provenance.get("source_type") not in {"user", "clinical", "research_dataset", "derived"}:
        issues.append(_issue(f"{path}.provenance.source_type", "is invalid"))
    return issues


def validate_user_input_package(package: dict[str, Any]) -> InputValidationReport:
    """Validate a package against the canonical v1 user-input contract.

    The function only inspects the supplied package metadata. It does not open
    ``uri`` values, inspect ``data/raw``, query a database, or infer absent data.
    """
    issues: list[ValidationIssue] = []
    subject_id = package.get("subject", {}).get("subject_id") if isinstance(package, dict) else None
    if not isinstance(package, dict):
        return InputValidationReport(False, None, (), {}, EvidenceStatus.UNAVAILABLE,
                                     (_issue("$", "must be an object"),))

    subject = package.get("subject")
    if not isinstance(subject, dict) or not isinstance(subject.get("subject_id"), str) or not subject["subject_id"].strip():
        issues.append(_issue("subject.subject_id", "is required"))
        subject_id = None

    acquisition = package.get("acquisition")
    timepoint_ids: list[str] = []
    if not isinstance(acquisition, dict):
        issues.append(_issue("acquisition", "is required and must be an object"))
    else:
        tp = acquisition.get("timepoint_id")
        if not isinstance(tp, str) or not tp.strip():
            issues.append(_issue("acquisition.timepoint_id", "is required"))
        else:
            timepoint_ids.append(tp)
        if not _is_iso_datetime(acquisition.get("acquisition_time")):
            issues.append(_issue("acquisition.acquisition_time", "must be ISO-8601 date-time"))
        if acquisition.get("laterality") not in {"left", "right", "bilateral", "unknown"}:
            issues.append(_issue("acquisition.laterality", "must be left, right, bilateral, or unknown"))

    inputs = package.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        issues.append(_issue("inputs", "must contain at least one input"))
        inputs = []

    reports: dict[str, ModalityReport] = {}
    for modality in MODALITIES:
        reports[modality] = ModalityReport(modality, ModalityStatus.MISSING)

    by_modality: dict[str, list[tuple[int, dict[str, Any], list[ValidationIssue]]]] = {}
    for i, item in enumerate(inputs):
        item_issues = _validate_input(item, i)
        if isinstance(item, dict) and item.get("kind") in MODALITIES:
            by_modality.setdefault(item["kind"], []).append((i, item, item_issues))
        issues.extend(item_issues)

    for modality, items in by_modality.items():
        valid_items = [x for x in items if not x[2]]
        item_ids = tuple(x[1]["input_id"] for x in valid_items if isinstance(x[1].get("input_id"), str))
        local_issues = tuple(issue for x in items for issue in x[2])
        if valid_items and not local_issues:
            status = ModalityStatus.AVAILABLE
        elif valid_items:
            status = ModalityStatus.PARTIAL
        else:
            status = ModalityStatus.INVALID
        reports[modality] = ModalityReport(modality, status, item_ids, local_issues)

    # Ground truth is evidence, not a prediction. Merely having it in the
    # package does not turn other observations into ground truth.
    gt = reports["ground_truth"]
    if gt.status == ModalityStatus.AVAILABLE:
        evidence_status = EvidenceStatus.GROUND_TRUTH
    elif any(r.status == ModalityStatus.AVAILABLE for r in reports.values()):
        evidence_status = EvidenceStatus.OBSERVED
    else:
        evidence_status = EvidenceStatus.UNAVAILABLE

    return InputValidationReport(
        valid=not issues,
        subject_id=subject_id,
        timepoint_ids=tuple(timepoint_ids),
        modalities=reports,
        evidence_status=evidence_status,
        issues=tuple(issues),
    )


def artifact_id(uri: str) -> str:
    """Return a deterministic identifier for a declared artifact URI/path."""
    return "artifact:" + str(PurePosixPath(uri))
