"""Map validated user inputs to downstream processing capabilities.

This is a routing/readiness layer, not a scientific inference engine. It never
fabricates missing modalities and never claims that a modality is scientifically
sufficient merely because its metadata is valid.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .input_validation import MODALITIES, ModalityStatus, InputValidationReport


@dataclass(frozen=True)
class ProcessingCapability:
    id: str
    name: str
    required_modalities: tuple[str, ...]
    optional_modalities: tuple[str, ...] = ()


CAPABILITIES = (
    ProcessingCapability("hand_geometry", "Hand geometry / macro analysis", ("hand_images",)),
    ProcessingCapability("hand_motion", "Hand video / motion analysis", ("hand_video",)),
    ProcessingCapability("hand_3d", "3D hand reconstruction", ("hand_3d",)),
    ProcessingCapability("tissue_structure", "WSI tissue analysis", ("tissue_wsi",)),
    ProcessingCapability("cell_structure", "Microscopy / cell morphology", ("microscopy",)),
    ProcessingCapability("single_cell_state", "Single-cell RNA biological state", ("single_cell_rna",)),
    ProcessingCapability("transcriptome_state", "Bulk RNA biological state", ("bulk_rna",)),
    ProcessingCapability("genomic_state", "Genomic variant / feature analysis", ("genomics",)),
    ProcessingCapability("proteomic_state", "Proteomic biological state", ("proteomics",)),
    ProcessingCapability("epigenetic_state", "Epigenetic biological state", ("epigenetics",)),
    ProcessingCapability("clinical_context", "Clinical context integration", ("clinical_context",)),
    ProcessingCapability("health_ground_truth", "Healthy / disease reference comparison", ("ground_truth",)),
    ProcessingCapability(
        "multimodal_cell_tissue",
        "Multimodal cell/tissue integration",
        ("tissue_wsi",),
        ("single_cell_rna", "proteomics", "epigenetics", "genomics", "ground_truth"),
    ),
)


def build_readiness(report: InputValidationReport) -> dict[str, Any]:
    statuses = {name: item.status.value for name, item in report.modalities.items()}
    capabilities = []
    for capability in CAPABILITIES:
        required = [statuses[m] for m in capability.required_modalities]
        optional_available = [m for m in capability.optional_modalities if statuses[m] == ModalityStatus.AVAILABLE.value]
        if all(s == ModalityStatus.AVAILABLE.value for s in required):
            status = "ready"
        elif any(s == ModalityStatus.PARTIAL.value for s in required):
            status = "partial"
        else:
            status = "unavailable"
        capabilities.append({
            "id": capability.id,
            "name": capability.name,
            "status": status,
            "required_modalities": list(capability.required_modalities),
            "optional_modalities": list(capability.optional_modalities),
            "available_optional_modalities": optional_available,
            "reason": None if status == "ready" else f"Required modality not available: {', '.join(capability.required_modalities)}",
        })

    available = [m for m in MODALITIES if statuses[m] == ModalityStatus.AVAILABLE.value]
    missing = [m for m in MODALITIES if statuses[m] == ModalityStatus.MISSING.value]
    return {
        "contract_valid": report.valid,
        "subject_id": report.subject_id,
        "timepoint_ids": list(report.timepoint_ids),
        "available_modalities": available,
        "missing_modalities": missing,
        "capabilities": capabilities,
        "policy": {
            "missing_modalities_are_not_fabricated": True,
            "readiness_is_not_scientific_validation": True,
            "ground_truth_is_reference_evidence": True,
        },
    }
