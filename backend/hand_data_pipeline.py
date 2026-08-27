from __future__ import annotations

"""Canonical data contracts and registries for hand digital-twin stages 1-10.

This module stores metadata and evidence lineage; it does not invent biological
measurements. Image/3-D/medical-imaging algorithms can consume these contracts
later and must register their outputs as derived objects with provenance.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "data" / "registry"
REGISTRY_PATH = REGISTRY_DIR / "hand_data_pipeline.json"
router = APIRouter(tags=["hand-data-pipeline-stages-1-10"])

VIEWS = ("front", "back", "thumb", "side_left", "side_right")
MODALITIES = {"photo", "mri", "ultrasound", "ct", "histology", "wsi", "microscopy", "metadata", "segmentation", "reconstruction"}
STAGE_NAMES = {
    1: "Data Dictionary",
    2: "Subject / Hand / Timepoint",
    3: "Provenance",
    4: "Quality / confidence",
    5: "Spatial coordinate system",
    6: "Photo acquisition",
    7: "Photo calibration",
    8: "Anatomical landmarks",
    9: "Segmentation",
    10: "3D reconstruction",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}
    try:
        value = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}
    except (OSError, json.JSONDecodeError):
        return {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}


def _write(value: dict[str, Any]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _record(stage: int, payload: dict[str, Any], *, status: str = "registered", evidence_ids: list[str] | None = None) -> dict[str, Any]:
    record = {
        "record_id": _id(f"stage{stage}"),
        "stage": stage,
        "stage_name": STAGE_NAMES[stage],
        "status": status,
        "created_at": now(),
        "evidence_ids": evidence_ids or [],
        **payload,
    }
    data = _read()
    data.setdefault("stage_records", []).append(record)
    _write(data)
    return record


class SubjectHandTimepoint(BaseModel):
    subject_id: str = Field(min_length=1)
    hand_id: str = Field(min_length=1)
    laterality: Literal["left", "right", "unknown"] = "unknown"
    timepoint_id: str = Field(min_length=1)
    acquisition_time: str | None = None
    subject_age_years: float | None = Field(default=None, ge=0, le=130)


class ProvenanceInput(BaseModel):
    source: str = Field(min_length=1)
    source_object_ids: list[str] = Field(default_factory=list)
    method: str | None = None
    method_version: str | None = None
    operator: str | None = None
    pipeline_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class QualityInput(BaseModel):
    status: Literal["unknown", "acceptable", "degraded", "rejected"] = "unknown"
    quality_score: float | None = Field(default=None, ge=0, le=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    flags: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class CoordinateInput(BaseModel):
    frame_id: str = Field(min_length=1)
    units: Literal["mm", "cm", "px", "voxel", "unknown"] = "mm"
    axes: tuple[str, str, str] = ("x", "y", "z")
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    handedness: Literal["right", "left", "unknown"] = "right"
    anatomical_orientation: str = "hand"
    parent_frame_id: str | None = None


class PhotoAcquisitionInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    view: Literal["front", "back", "thumb", "side_left", "side_right"]
    asset_id: str | None = None
    filename: str | None = None
    camera: str | None = None
    lens: str | None = None
    focal_length_mm: float | None = Field(default=None, gt=0)
    distance_mm: float | None = Field(default=None, gt=0)
    lighting: dict[str, Any] = Field(default_factory=dict)
    scale_reference: dict[str, Any] = Field(default_factory=dict)
    orientation: dict[str, Any] = Field(default_factory=dict)
    acquisition_time: str | None = None


class CalibrationInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    asset_id: str
    model: Literal["none", "pinhole", "opencv", "fisheye", "unknown"] = "unknown"
    camera_matrix: list[list[float]] | None = None
    distortion_coefficients: list[float] = Field(default_factory=list)
    reprojection_error_px: float | None = Field(default=None, ge=0)
    scale_mm_per_px: float | None = Field(default=None, gt=0)
    method: str = "not_specified"


class Landmark(BaseModel):
    landmark_id: str
    name: str
    x: float
    y: float
    z: float | None = None
    coordinate_frame: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class LandmarkSetInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    asset_id: str
    landmarks: list[Landmark] = Field(min_length=1)


class SegmentationInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_object_id: str
    segmentation_id: str | None = None
    labels: list[str] = Field(min_length=1)
    mask_asset_id: str | None = None
    method: str | None = None
    model_version: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ReconstructionInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_object_ids: list[str] = Field(min_length=2)
    mesh_asset_id: str | None = None
    texture_asset_id: str | None = None
    coordinate_frame: str
    scale_unit: Literal["mm", "cm", "unknown"] = "mm"
    method: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ImagingInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: Literal["mri", "ultrasound", "ct"]
    asset_id: str
    study_id: str | None = None
    acquisition_metadata: dict[str, Any] = Field(default_factory=dict)
    voxel_spacing: tuple[float, float, float] | None = None
    coordinate_frame: str | None = None


class RegistrationInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_object_id: str
    target_object_id: str
    source_frame: str
    target_frame: str
    transform_type: Literal["rigid", "affine", "deformable", "unknown"] = "unknown"
    transform: dict[str, Any] = Field(default_factory=dict)
    registration_error: float | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)


class HistologyInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    sample_id: str
    asset_id: str
    anatomical_region: str
    tissue_type: str
    staining: str
    sample_location: dict[str, Any]
    slide_metadata: dict[str, Any] = Field(default_factory=dict)
    coordinate_frame: str | None = None


class TissueSegmentationInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    sample_id: str
    source_asset_id: str
    labels: list[str] = Field(min_length=1)
    mask_asset_id: str | None = None
    method: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class TissuePathologyInput(BaseModel):
    subject_id: str
    hand_id: str
    timepoint_id: str
    sample_id: str
    region_id: str
    classification: Literal["normal", "abnormal", "inflammatory", "fibrotic", "degenerative", "pathological", "unknown"]
    evidence_object_ids: list[str] = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    method: str
    interpretation: str | None = None


@router.get("/api/hand/stages")
def stage_catalog() -> dict[str, Any]:
    return {"schema": "testhp.hand_pipeline.v1", "stages": [{"stage": n, "name": name} for n, name in STAGE_NAMES.items()]}


@router.get("/api/hand/data-model")
def data_model() -> dict[str, Any]:
    return {
        "schema": "testhp.hand_pipeline.v1",
        "hierarchy": ["Subject", "Hand", "Timepoint", "Acquisition", "Dataset", "Observation"],
        "required_envelope": ["id", "source", "created_at", "acquisition_time", "timepoint", "provenance", "quality", "confidence"],
        "views": list(VIEWS),
        "coordinate_system": "HAND_COORDINATE_SYSTEM",
        "rule": "No biological conclusion is valid without linked evidence, provenance, quality and confidence.",
    }


@router.get("/api/hand/data-registry")
def data_registry(subject_id: str | None = None, timepoint_id: str | None = None) -> dict[str, Any]:
    data = _read()
    objects = data.get("objects", [])
    if subject_id:
        objects = [x for x in objects if x.get("subject_id") == subject_id]
    if timepoint_id:
        objects = [x for x in objects if x.get("timepoint_id") == timepoint_id]
    records = data.get("stage_records", [])
    if subject_id:
        records = [x for x in records if x.get("subject_id") == subject_id]
    return {"schema": data.get("schema"), "objects": objects, "stage_records": records, "counts": {"objects": len(objects), "stage_records": len(records)}}


@router.post("/api/hand/subjects")
def register_subject(request: SubjectHandTimepoint) -> dict[str, Any]:
    data = _read()
    subject = data.setdefault("subjects", {}).setdefault(request.subject_id, {"subject_id": request.subject_id, "hands": {}, "timepoints": {}})
    subject["hands"][request.hand_id] = {"hand_id": request.hand_id, "laterality": request.laterality}
    subject["timepoints"][request.timepoint_id] = {"timepoint_id": request.timepoint_id, "acquisition_time": request.acquisition_time, "subject_age_years": request.subject_age_years}
    _write(data)
    return _record(2, {"subject_id": request.subject_id, "hand_id": request.hand_id, "timepoint_id": request.timepoint_id, "entity": _dump(request)})


@router.post("/api/hand/provenance")
def register_provenance(request: ProvenanceInput) -> dict[str, Any]:
    return _record(3, {"provenance": _dump(request), "subject_id": None})


@router.post("/api/hand/quality")
def register_quality(request: QualityInput) -> dict[str, Any]:
    return _record(4, {"quality": _dump(request), "confidence": request.confidence, "subject_id": None})


@router.post("/api/hand/spatial-frame")
def register_spatial_frame(request: CoordinateInput) -> dict[str, Any]:
    return _record(5, {"frame": _dump(request), "coordinate_system": "HAND_COORDINATE_SYSTEM", "subject_id": None})


@router.post("/api/hand/photo-acquisitions")
def register_photo_acquisition(request: PhotoAcquisitionInput) -> dict[str, Any]:
    payload = _dump(request)
    payload["source"] = "photo"
    payload["required_view_set"] = list(VIEWS)
    return _record(6, payload, status="acquired" if request.asset_id else "metadata_only")


@router.post("/api/hand/photo-calibrations")
def register_photo_calibration(request: CalibrationInput) -> dict[str, Any]:
    status = "calibrated" if request.camera_matrix or request.scale_mm_per_px else "metadata_only"
    return _record(7, {**_dump(request), "source": "photo_calibration"}, status=status)


@router.post("/api/hand/landmarks")
def register_landmarks(request: LandmarkSetInput) -> dict[str, Any]:
    return _record(8, {**_dump(request), "source": "anatomical_landmarks"}, status="observed")


@router.post("/api/hand/segmentations")
def register_segmentation(request: SegmentationInput) -> dict[str, Any]:
    return _record(9, {**_dump(request), "source": "segmentation"}, status="computed" if request.mask_asset_id else "metadata_only", evidence_ids=[request.source_object_id])


@router.post("/api/hand/reconstructions")
def register_reconstruction(request: ReconstructionInput) -> dict[str, Any]:
    if len(request.source_object_ids) < 2:
        raise HTTPException(status_code=422, detail="3D reconstruction requires at least two source objects")
    return _record(10, {**_dump(request), "source": "reconstruction", "lineage": request.source_object_ids}, status="computed" if request.mesh_asset_id else "planned", evidence_ids=request.source_object_ids)


@router.post("/api/hand/imaging")
def register_imaging(request: ImagingInput) -> dict[str, Any]:
    if request.modality not in {"mri", "ultrasound", "ct"}:
        raise HTTPException(status_code=400, detail="unsupported internal-imaging modality")
    return _record(11, {**_dump(request), "source": request.modality}, status="acquired")


@router.post("/api/hand/registrations")
def register_registration(request: RegistrationInput) -> dict[str, Any]:
    if not request.transform:
        return _record(12, {**_dump(request), "source": "multimodal_registration"}, status="unregistered", evidence_ids=[request.source_object_id, request.target_object_id])
    return _record(12, {**_dump(request), "source": "multimodal_registration"}, status="registered", evidence_ids=[request.source_object_id, request.target_object_id])


@router.post("/api/hand/histology")
def register_histology(request: HistologyInput) -> dict[str, Any]:
    return _record(13, {**_dump(request), "source": "histology"}, status="acquired")


@router.post("/api/hand/tissue-segmentations")
def register_tissue_segmentation(request: TissueSegmentationInput) -> dict[str, Any]:
    return _record(14, {**_dump(request), "source": "tissue_segmentation"}, status="computed" if request.mask_asset_id else "metadata_only", evidence_ids=[request.source_asset_id])


@router.post("/api/hand/tissue-pathology")
def register_tissue_pathology(request: TissuePathologyInput) -> dict[str, Any]:
    if not request.evidence_object_ids:
        raise HTTPException(status_code=422, detail="pathology classification requires evidence_object_ids")
    return _record(15, {**_dump(request), "source": "tissue_pathology", "interpretation_boundary": "research_annotation_requires_review"}, status="annotated", evidence_ids=request.evidence_object_ids)


@router.get("/api/hand/validate")
def validate_hand_get(subject_id: str = "own_cohort", timepoint: str = "T0", session_id: str = "session-001") -> dict[str, Any]:
    """GET counterpart for browser/runtime probes.

    Contract validation and real-data validation are intentionally separate.
    """
    contract = {"valid": True, "errors": [], "required_views": list(VIEWS), "schema": "testhp.hand_pipeline.v1"}
    data = _read()
    subject = data.get("subjects", {}).get(subject_id)
    registered_timepoint = bool(subject and timepoint in subject.get("timepoints", {}))
    stage6 = [r for r in data.get("stage_records", []) if r.get("stage") == 6 and r.get("subject_id") == subject_id and r.get("timepoint_id") == timepoint]
    available_views = sorted({r.get("view") for r in stage6 if r.get("view") in VIEWS and r.get("asset_id")})
    real = {"valid": len(available_views) == len(VIEWS), "errors": [] if len(available_views) == len(VIEWS) else [f"missing photo views: {', '.join(v for v in VIEWS if v not in available_views)}"], "subject_registered": registered_timepoint, "available_views": available_views, "missing_views": [v for v in VIEWS if v not in available_views]}
    return {"valid": contract["valid"] and real["valid"], "contract": contract, "data": real, "subject_id": subject_id, "timepoint": timepoint, "session_id": session_id, "validation_scope": {"contract": "schema_and_required_fields", "data": "locally_registered_real_evidence"}}


@router.post("/api/hand/validate-contract")
def validate_contract(request: SubjectHandTimepoint) -> dict[str, Any]:
    return {"valid": True, "errors": [], "schema": "testhp.hand_pipeline.v1", "validated": _dump(request)}


def register_hand_data_pipeline(app: Any) -> None:
    app.include_router(router)
