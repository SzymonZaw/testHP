from __future__ import annotations

"""Canonical contracts for digital-twin stages 11-20."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "registry" / "hand_data_pipeline.json"
router = APIRouter(tags=["hand-digital-twin-stages-11-20"])
STAGE_NAMES = {11: "Cell segmentation", 12: "Cell identification", 13: "Cell morphology", 14: "Cell state", 15: "scRNA-seq", 16: "Spatial transcriptomics", 17: "Proteomics", 18: "Epigenetics", 19: "Multi-omics integration", 20: "Longitudinal data"}
CELL_TYPES = ("keratinocyte", "fibroblast", "endothelial", "immune", "muscle", "nerve-associated", "other", "unknown")
CELL_STATES = ("normal", "stressed", "senescent", "apoptotic", "proliferating", "inflammatory", "pathological", "unknown")

def now() -> str: return datetime.now(timezone.utc).isoformat()
def read_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists(): return {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}
    try:
        value = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")); return value if isinstance(value, dict) else {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}
    except (OSError, json.JSONDecodeError): return {"schema": "testhp.hand_pipeline.v1", "subjects": {}, "objects": [], "stage_records": []}
def write_registry(value: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True); tmp = REGISTRY_PATH.with_suffix(".tmp"); tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"); tmp.replace(REGISTRY_PATH)
def record(stage: int, payload: dict[str, Any], evidence_ids: list[str] | None = None, status: str = "registered") -> dict[str, Any]:
    item = {"record_id": f"stage{stage}_{uuid.uuid4().hex[:12]}", "stage": stage, "stage_name": STAGE_NAMES[stage], "status": status, "created_at": now(), "evidence_ids": evidence_ids or [], **payload}; data = read_registry(); data.setdefault("stage_records", []).append(item); write_registry(data); return item

class Envelope(BaseModel):
    subject_id: str; hand_id: str; timepoint_id: str; source: str; acquisition_time: str | None = None; provenance: dict[str, Any] = Field(default_factory=dict); quality: dict[str, Any] = Field(default_factory=dict); confidence: float | None = Field(default=None, ge=0, le=1)
class CellObject(BaseModel):
    cell_id: str; position: tuple[float, float, float]; tissue: str; morphology: dict[str, Any] = Field(default_factory=dict); nucleus: dict[str, Any] = Field(default_factory=dict); neighbors: list[str] = Field(default_factory=list); coordinate_frame: str; confidence: float | None = Field(default=None, ge=0, le=1)
class CellSegmentationInput(Envelope):
    source_asset_id: str; cells: list[CellObject] = Field(min_length=1); method: str; model_version: str | None = None; mask_asset_id: str | None = None
class CellIdentificationInput(Envelope):
    cell_id: str; cell_type: Literal["keratinocyte", "fibroblast", "endothelial", "immune", "muscle", "nerve-associated", "other", "unknown"]; evidence_object_ids: list[str] = Field(min_length=1); method: str; confidence: float | None = Field(default=None, ge=0, le=1); markers: dict[str, Any] = Field(default_factory=dict)
class CellMorphologyInput(Envelope):
    cell_id: str; area: float | None = Field(default=None, ge=0); perimeter: float | None = Field(default=None, ge=0); circularity: float | None = Field(default=None, ge=0); aspect_ratio: float | None = Field(default=None, ge=0); nucleus_cytoplasm_ratio: float | None = Field(default=None, ge=0); cell_density: float | None = Field(default=None, ge=0); neighbor_relationships: dict[str, Any] = Field(default_factory=dict); measurement_units: dict[str, str] = Field(default_factory=dict); evidence_object_ids: list[str] = Field(min_length=1)
class CellStateInput(Envelope):
    cell_id: str; state: Literal["normal", "stressed", "senescent", "apoptotic", "proliferating", "inflammatory", "pathological", "unknown"]; evidence_object_ids: list[str] = Field(min_length=1); method: str; confidence: float | None = Field(default=None, ge=0, le=1); biomarkers: dict[str, Any] = Field(default_factory=dict)
class ScRNAInput(Envelope):
    dataset_id: str; assay_id: str; matrix_asset_id: str; matrix_format: str; cell_ids: list[str] = Field(min_length=1); gene_count: int | None = Field(default=None, ge=0); metadata_asset_id: str | None = None; platform: str | None = None; preprocessing: dict[str, Any] = Field(default_factory=dict)
class SpatialTranscriptomicsInput(Envelope):
    dataset_id: str; assay_id: str; expression_asset_id: str; spatial_coordinates_asset_id: str; coordinate_frame: str; resolution: dict[str, Any] = Field(default_factory=dict); cell_or_spot_ids: list[str] = Field(min_length=1); method: str; confidence: float | None = Field(default=None, ge=0, le=1)
class ProteomicsInput(Envelope):
    dataset_id: str; assay_id: str; abundance_asset_id: str; protein_count: int | None = Field(default=None, ge=0); modifications_asset_id: str | None = None; spatial_context_asset_id: str | None = None; platform: str | None = None; normalization: dict[str, Any] = Field(default_factory=dict)
class EpigeneticsInput(Envelope):
    dataset_id: str; assay_id: str; assay_type: Literal["dna_methylation", "chromatin", "regulatory_state", "other"]; data_asset_id: str; feature_count: int | None = Field(default=None, ge=0); platform: str | None = None; preprocessing: dict[str, Any] = Field(default_factory=dict)
class MultiOmicsInput(Envelope):
    integration_id: str; modality_object_ids: dict[str, list[str]]; integration_method: str; spatial_resolution: str | None = None; temporal_resolution: str | None = None; alignment_quality: float | None = Field(default=None, ge=0, le=1); confidence: float | None = Field(default=None, ge=0, le=1)
class LongitudinalInput(Envelope):
    trajectory_id: str; observation_object_ids: list[str] = Field(min_length=2); ordered_timepoints: list[str] = Field(min_length=2); modalities: list[str] = Field(min_length=1); linkage_method: str; comparability: dict[str, Any] = Field(default_factory=dict); confidence: float | None = Field(default=None, ge=0, le=1)

@router.get("/api/hand/stages-11-20")
def stage_catalog_11_20() -> dict[str, Any]: return {"schema": "testhp.hand_pipeline.v1", "stages": [{"stage": n, "name": name} for n, name in STAGE_NAMES.items()], "cell_types": list(CELL_TYPES), "cell_states": list(CELL_STATES)}
@router.post("/api/hand/cells/segmentations")
def register_cell_segmentation(request: CellSegmentationInput) -> dict[str, Any]: return record(11, {**request.model_dump(), "source": "cell_segmentation", "cell_count": len(request.cells)}, [request.source_asset_id], "computed")
@router.post("/api/hand/cells/identifications")
def register_cell_identification(request: CellIdentificationInput) -> dict[str, Any]: return record(12, {**request.model_dump(), "source": "cell_identification"}, request.evidence_object_ids, "classified")
@router.post("/api/hand/cells/morphology")
def register_cell_morphology(request: CellMorphologyInput) -> dict[str, Any]: return record(13, {**request.model_dump(), "source": "cell_morphology"}, request.evidence_object_ids, "measured")
@router.post("/api/hand/cells/states")
def register_cell_state(request: CellStateInput) -> dict[str, Any]: return record(14, {**request.model_dump(), "source": "cell_state_estimation"}, request.evidence_object_ids, "estimated")
@router.post("/api/hand/molecular/scrna")
def register_scrna(request: ScRNAInput) -> dict[str, Any]: return record(15, {**request.model_dump(), "source": "scRNA-seq"}, [request.matrix_asset_id], "acquired")
@router.post("/api/hand/molecular/spatial-transcriptomics")
def register_spatial_transcriptomics(request: SpatialTranscriptomicsInput) -> dict[str, Any]: return record(16, {**request.model_dump(), "source": "spatial_transcriptomics"}, [request.expression_asset_id, request.spatial_coordinates_asset_id], "acquired")
@router.post("/api/hand/molecular/proteomics")
def register_proteomics(request: ProteomicsInput) -> dict[str, Any]: return record(17, {**request.model_dump(), "source": "proteomics"}, [request.abundance_asset_id] + ([request.modifications_asset_id] if request.modifications_asset_id else []), "acquired")
@router.post("/api/hand/molecular/epigenetics")
def register_epigenetics(request: EpigeneticsInput) -> dict[str, Any]: return record(18, {**request.model_dump(), "source": "epigenetics"}, [request.data_asset_id], "acquired")
@router.post("/api/hand/molecular/multi-omics")
def register_multi_omics(request: MultiOmicsInput) -> dict[str, Any]: return record(19, {**request.model_dump(), "source": "multi_omics_integration"}, [item for values in request.modality_object_ids.values() for item in values], "integrated")
@router.post("/api/hand/longitudinal")
def register_longitudinal(request: LongitudinalInput) -> dict[str, Any]: return record(20, {**request.model_dump(), "source": "longitudinal"}, request.observation_object_ids, "linked")

def register_hand_cellular_pipeline(app: Any) -> None:
    app.include_router(router)
    from .reference_geometry_proxy import register_reference_geometry_proxy
    register_reference_geometry_proxy(app)
