"""Stage 15-20-ready analysis contracts and deterministic pipeline interfaces.

These are data/validation interfaces, not clinical ML models. Real model adapters
must provide externally validated weights and datasets before clinical use.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CellState(str, Enum):
    HEALTHY = "healthy"
    ALTERED = "altered"
    STRESSED = "stressed"
    SENESCENT = "senescent"
    DAMAGED = "damaged"
    PATHOLOGICAL = "pathological"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CellInstance:
    cell_id: str
    centroid_um: tuple[float, float]
    boundary: tuple[tuple[float, float], ...]
    segmentation_confidence: float | None = None


@dataclass(frozen=True)
class SegmentationResult:
    segmentation_id: str
    image_id: str
    algorithm_id: str
    algorithm_version: str
    nuclei: tuple[CellInstance, ...] = ()
    cells: tuple[CellInstance, ...] = ()
    expert_annotation_id: str | None = None

    def validate(self) -> None:
        if not self.segmentation_id or not self.image_id or not self.algorithm_id:
            raise ValueError("segmentation identity is required")
        for cell in (*self.nuclei, *self.cells):
            if cell.segmentation_confidence is not None and not 0 <= cell.segmentation_confidence <= 1:
                raise ValueError("segmentation confidence must be between 0 and 1")


@dataclass(frozen=True)
class CellTypeAssessment:
    cell_id: str
    cell_type: str
    confidence: float | None
    marker_values: dict[str, float] = None  # type: ignore[assignment]
    morphology: dict[str, float] = None  # type: ignore[assignment]
    molecular_features: dict[str, float] = None  # type: ignore[assignment]
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "marker_values", self.marker_values or {})
        object.__setattr__(self, "morphology", self.morphology or {})
        object.__setattr__(self, "molecular_features", self.molecular_features or {})

    def validate(self) -> None:
        if not self.cell_id or not self.cell_type:
            raise ValueError("cell type identity is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class CellHealthAssessment:
    cell_id: str
    state: CellState
    deviation_score: float | None
    biomarkers: dict[str, float]
    confidence: float | None
    evidence_ids: tuple[str, ...] = ()
    expert_review_status: str = "not_reviewed"

    def validate(self) -> None:
        if not self.cell_id:
            raise ValueError("cell identity is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class PathologySignal:
    signal_id: str
    spatial_id: str
    abnormality: str
    severity: str
    confidence: float | None
    evidence_ids: tuple[str, ...] = ()
    expert_review_status: str = "not_reviewed"


class CellAnalysisPipeline:
    """Orchestration boundary; concrete ML/image implementations are adapters."""

    def preprocess(self, microscopy: Any) -> Any:
        return microscopy

    def segment(self, preprocessed: Any) -> SegmentationResult:
        raise NotImplementedError("connect a validated segmentation model")

    def classify_cell_type(self, cell: CellInstance) -> CellTypeAssessment:
        raise NotImplementedError("connect a validated cell-type model")

    def assess_health(self, cell: CellInstance) -> CellHealthAssessment:
        raise NotImplementedError("connect a validated cell-health model")

    def detect_pathology(self, cells: tuple[CellInstance, ...]) -> tuple[PathologySignal, ...]:
        raise NotImplementedError("connect a validated pathology model")
