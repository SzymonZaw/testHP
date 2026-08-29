"""API endpoints for validating a declared multimodal user input package.

The validator is metadata-only: it never opens declared URIs, scans data/raw,
or queries the database. Physical file ingestion remains a separate concern.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.input_validation import validate_user_input_package

router = APIRouter(prefix="/api/user-input", tags=["user-input"])


class UserInputPackageRequest(BaseModel):
    package: dict[str, Any] = Field(..., description="Canonical v1 user-input package")


def _report_to_dict(report: Any) -> dict[str, Any]:
    return {
        "valid": report.valid,
        "subject_id": report.subject_id,
        "timepoint_ids": list(report.timepoint_ids),
        "evidence_status": report.evidence_status.value,
        "available_modalities": list(report.available_modalities),
        "missing_modalities": list(report.missing_modalities),
        "modalities": {
            modality: {
                "status": item.status.value,
                "input_ids": list(item.input_ids),
                "issues": [{"path": issue.path, "message": issue.message} for issue in item.issues],
            }
            for modality, item in report.modalities.items()
        },
        "issues": [{"path": issue.path, "message": issue.message} for issue in report.issues],
        "policy": {
            "uri_accessed": False,
            "raw_data_scanned": False,
            "database_queried": False,
            "missing_data_fabricated": False,
        },
    }


@router.post("/validate")
def validate_user_input(request: UserInputPackageRequest) -> dict[str, Any]:
    """Return deterministic modality coverage and validation state."""
    return _report_to_dict(validate_user_input_package(request.package))
