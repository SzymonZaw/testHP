"""Resolve research capabilities from validated user-supplied modalities.

This module is deliberately conservative: a capability is available only when
its declared input modalities are present and valid. Missing modalities are
reported as unavailable/insufficient evidence and never treated as negatives.
"""

from __future__ import annotations

from typing import Any


CAPABILITY_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "hand_structure": {"requires_any": {"hand_images", "hand_3d"}, "level": "macro"},
    "hand_motion": {"requires_any": {"hand_video"}, "level": "macro"},
    "tissue_morphology": {"requires_any": {"tissue_wsi", "microscopy"}, "level": "tissue"},
    "single_cell_state": {"requires_any": {"single_cell_rna", "microscopy"}, "level": "cell"},
    "genomic_state": {"requires_any": {"genomics"}, "level": "molecular"},
    "proteomic_state": {"requires_any": {"proteomics"}, "level": "molecular"},
    "epigenetic_state": {"requires_any": {"epigenetics"}, "level": "molecular"},
    "molecular_state": {"requires_any": {"single_cell_rna", "bulk_rna", "genomics", "proteomics", "epigenetics"}, "level": "molecular"},
    "biological_age_research": {
        "requires_any": {"single_cell_rna", "bulk_rna", "proteomics", "epigenetics", "tissue_wsi", "microscopy"},
        "level": "research",
        "warning": "Availability of age-related measurements does not imply a validated biological-age clock.",
    },
    "health_disease_research": {
        "requires_any": {"tissue_wsi", "microscopy", "single_cell_rna", "bulk_rna", "proteomics", "epigenetics", "clinical_context", "ground_truth"},
        "level": "research",
        "warning": "Health/disease interpretation requires a validated reference model and appropriate ground truth.",
    },
}


def resolve_capabilities(available_modalities: list[str] | tuple[str, ...] | set[str]) -> dict[str, Any]:
    available = set(available_modalities)
    capabilities: dict[str, Any] = {}
    for name, spec in CAPABILITY_REQUIREMENTS.items():
        matched = sorted(available & set(spec["requires_any"]))
        ready = bool(matched)
        capabilities[name] = {
            "status": "available" if ready else "insufficient_evidence",
            "level": spec["level"],
            "matched_modalities": matched,
            "required_any": sorted(spec["requires_any"]),
            "warning": spec.get("warning"),
        }
    return capabilities


def build_user_analysis_plan(report: Any) -> dict[str, Any]:
    available = list(report.available_modalities)
    capabilities = resolve_capabilities(available)
    unavailable = [name for name, item in capabilities.items() if item["status"] != "available"]
    limitations: list[str] = []
    if report.missing_modalities:
        limitations.append("Missing modalities are unknown and are not interpreted as negative findings.")
    if report.evidence_status.value != "ground_truth":
        limitations.append("The submitted package does not establish ground truth for model validation.")
    if "biological_age_research" in capabilities:
        limitations.append(capabilities["biological_age_research"]["warning"])
    if "health_disease_research" in capabilities:
        limitations.append(capabilities["health_disease_research"]["warning"])
    return {
        "observed_inputs": available,
        "available_analyses": [name for name, item in capabilities.items() if item["status"] == "available"],
        "unavailable_analyses": unavailable,
        "capabilities": capabilities,
        "limitations": limitations,
    }
