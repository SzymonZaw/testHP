from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineRoute:
    input_kind: str
    stage: str
    modules: tuple[str, ...]
    notes: str


INPUT_PIPELINE_MAP: dict[str, PipelineRoute] = {
    "hand_images": PipelineRoute(
        "hand_images", "macro", ("backend.photo_reconstruction_routes", "analysis.morphology_analysis"),
        "Images are the minimum input; morphology is downstream and must not be treated as a diagnosis.",
    ),
    "hand_video": PipelineRoute(
        "hand_video", "macro_enhanced", ("backend.photo_reconstruction_routes",),
        "Video is an enhanced temporal input; the exact reconstruction entry point must validate the uploaded format.",
    ),
    "hand_3d": PipelineRoute(
        "hand_3d", "macro_enhanced", ("frontend.digital-twin.spatial-target-canonicalizer",),
        "3D geometry should feed spatial canonicalization before downstream analysis.",
    ),
    "tissue_wsi": PipelineRoute(
        "tissue_wsi", "tissue", ("analysis.tissue_analysis", "analysis.pathology_analysis"),
        "Whole-slide tissue data supports tissue morphology/pathology analysis only when the appropriate preprocessing is available.",
    ),
    "microscopy": PipelineRoute(
        "microscopy", "cellular", ("analysis.morphology_analysis", "analysis.cell_analysis"),
        "Microscopy requires segmentation/quality control before cell-level morphology is meaningful.",
    ),
    "single_cell_rna": PipelineRoute(
        "single_cell_rna", "cellular", ("analysis.rna_analysis", "analysis.cell_analysis"),
        "Single-cell RNA supports transcriptomic cellular characterization; it does not by itself establish clinical disease.",
    ),
    "molecular_assay": PipelineRoute(
        "molecular_assay", "molecular", ("analysis.rna_analysis",),
        "Generic molecular assays require a modality-specific adapter before any analysis module is selected.",
    ),
    "genomics": PipelineRoute(
        "genomics", "molecular", ("analysis.risk_analysis",),
        "Genomic risk analysis requires an explicit assay adapter and validated interpretation model.",
    ),
    "proteomics": PipelineRoute(
        "proteomics", "molecular", (),
        "No dedicated proteomics analysis module was identified in the current branch; keep this input accepted but unprocessed.",
    ),
}


def routes_for_inputs(input_kinds: set[str] | list[str] | tuple[str, ...]) -> list[PipelineRoute]:
    """Return deterministic routes for known input kinds; unknown kinds are omitted."""
    return [INPUT_PIPELINE_MAP[kind] for kind in sorted(set(input_kinds)) if kind in INPUT_PIPELINE_MAP]


def unmapped_inputs(input_kinds: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    """Return supplied kinds that have no declared pipeline route."""
    return sorted(set(input_kinds) - INPUT_PIPELINE_MAP.keys())
