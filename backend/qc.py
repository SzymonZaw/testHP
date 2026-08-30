"""Quality-control boundary shared by modality pipelines."""
from __future__ import annotations

from .analysis_orchestrator import QCResult

SUPPORTED_MODALITIES = ("hand_images", "hand_video", "hand_3d", "tissue_wsi", "rna", "proteomics", "epigenetics", "genomics")


def qc_status(modality: str, value: object) -> QCResult:
    if modality not in SUPPORTED_MODALITIES:
        return QCResult(modality, "unusable", ("unsupported_modality",))
    if value is None:
        return QCResult(modality, "missing")
    if isinstance(value, dict) and value.get("qc_status") == "unusable":
        return QCResult(modality, "unusable", tuple(value.get("reasons", ())))
    return QCResult(modality, "usable")
