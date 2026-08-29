from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Capability:
    kind: str
    level: str
    required: bool
    status: str
    accepted_formats: tuple[str, ...]
    output: str
    notes: str = ""


CAPABILITIES: dict[str, Capability] = {
    "hand_images": Capability("hand_images", "macro", True, "available", ("jpg", "jpeg", "png", "webp"), "macro_observations"),
    "hand_video": Capability("hand_video", "macro", False, "available", ("mp4", "mov", "webm"), "temporal_macro_observations"),
    "hand_3d": Capability("hand_3d", "macro", False, "partial", ("obj", "ply", "stl", "glb", "gltf"), "canonical_hand_geometry", "Requires validated 3D ingestion/canonicalization.") ,
    "tissue_wsi": Capability("tissue_wsi", "tissue", False, "partial", ("svs", "ndpi", "tif", "tiff"), "tissue_regions", "Segmentation/annotation must precede cell claims."),
    "microscopy": Capability("microscopy", "cellular", False, "partial", ("tif", "tiff", "png", "jpg"), "cell_candidates", "Requires segmentation and QC."),
    "single_cell_rna": Capability("single_cell_rna", "cellular", False, "partial", ("h5ad", "mtx", "tsv", "csv"), "cell_transcriptomic_features", "Does not establish disease by itself."),
    "bulk_rna": Capability("bulk_rna", "molecular", False, "partial", ("tsv", "csv", "txt", "h5", "h5ad"), "molecular_features"),
    "genomics": Capability("genomics", "molecular", False, "planned", ("vcf", "bcf", "bam", "cram"), "genomic_features", "Clinical interpretation is deliberately not inferred without a validated model."),
    "proteomics": Capability("proteomics", "molecular", False, "planned", ("csv", "tsv", "mzml", "mzidentml"), "protein_features"),
    "epigenetics": Capability("epigenetics", "molecular", False, "planned", ("bed", "bedgraph", "bigwig", "csv", "tsv"), "epigenetic_features"),
    "clinical_context": Capability("clinical_context", "context", False, "contract_only", ("json", "csv"), "clinical_context"),
    "ground_truth": Capability("ground_truth", "validation", False, "contract_only", ("json", "csv"), "label_evidence"),
}


@dataclass
class Evidence:
    source_id: str
    source_type: str
    level: str
    target_id: str | None = None
    label: str | None = None
    confidence: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class BiologicalAssessment:
    target_id: str
    status: str  # observed | inferred | unavailable | not_validated
    biological_age_years: float | None
    health_state: str | None
    confidence: float | None
    evidence: list[Evidence]
    limitations: list[str]


@dataclass
class ScaleNode:
    node_id: str
    level: str  # macro | tissue | cellular | molecular
    parent_id: str | None
    relation: str
    source_ids: list[str] = field(default_factory=list)


@dataclass
class TwinGraph:
    subject_id: str
    timepoint_id: str
    nodes: list[ScaleNode]


def capability_report(input_kinds: set[str] | list[str]) -> list[Capability]:
    """Return capabilities without pretending planned analyses are implemented."""
    return [CAPABILITIES[k] for k in sorted(set(input_kinds)) if k in CAPABILITIES]
