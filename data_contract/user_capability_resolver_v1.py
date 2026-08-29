"""Resolve research capabilities from QC-accepted user inputs.

This layer answers "what can we analyse from what the user supplied?" It does
not inspect scientific file contents and does not infer missing measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CAPABILITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "macro_hand_analysis": ("hand_images",),
    "hand_motion_analysis": ("hand_video",),
    "metric_3d_hand_analysis": ("hand_3d",),
    "tissue_morphology_analysis": ("tissue_wsi", "microscopy"),
    "cell_segmentation_and_localization": ("tissue_wsi", "microscopy"),
    "single_cell_transcriptomic_analysis": ("single_cell_rna",),
    "genomic_variant_analysis": ("genomics",),
    "proteomic_state_analysis": ("proteomics",),
    "epigenetic_state_analysis": ("epigenetics",),
    "multimodal_molecular_state": ("single_cell_rna", "genomics", "proteomics", "epigenetics"),
}

# A requirement group means that at least one member is sufficient for a
# morphology/tissue capability, while molecular fusion requires all members.
ANY_OF = {"tissue_morphology_analysis", "cell_segmentation_and_localization"}


@dataclass(frozen=True)
class Capability:
    capability_id: str
    status: str
    required_kinds: tuple[str, ...]
    accepted_input_ids: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    output_domains: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "status": self.status,
            "required_kinds": list(self.required_kinds),
            "accepted_input_ids": list(self.accepted_input_ids),
            "blocking_reasons": list(self.blocking_reasons),
            "output_domains": list(self.output_domains),
        }


def _accepted_inputs(package: dict[str, Any]) -> dict[str, list[str]]:
    accepted: dict[str, list[str]] = {}
    for item in package.get("inputs", []):
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        input_id = item.get("input_id")
        if kind and input_id:
            accepted.setdefault(kind, []).append(input_id)
    return accepted


def resolve_capabilities(package: dict[str, Any], accepted_kinds: set[str] | None = None) -> dict[str, Any]:
    """Return capabilities based only on inputs accepted by the ingestion/QC layer.

    ``accepted_kinds`` should normally come from ``validate_user_package``.
    When omitted, the function conservatively treats structurally valid input
    entries as accepted metadata, not as scientifically validated evidence.
    """
    by_kind = _accepted_inputs(package)
    if accepted_kinds is not None:
        by_kind = {k: v for k, v in by_kind.items() if k in accepted_kinds}

    capabilities: list[Capability] = []
    for capability_id, required in CAPABILITY_REQUIREMENTS.items():
        present = [k for k in required if k in by_kind]
        if capability_id in ANY_OF:
            available = bool(present)
            partial = False
        else:
            available = len(present) == len(required)
            partial = bool(present) and not available

        if available:
            status = "available"
            reasons: tuple[str, ...] = ()
        elif partial:
            status = "partial"
            reasons = (f"Missing accepted modality: {', '.join(k for k in required if k not in by_kind)}",)
        else:
            status = "unavailable"
            reasons = (f"No accepted input for: {', '.join(required)}",)

        domain = "molecular" if capability_id in {
            "single_cell_transcriptomic_analysis", "genomic_variant_analysis",
            "proteomic_state_analysis", "epigenetic_state_analysis",
            "multimodal_molecular_state",
        } else "cellular" if "cell" in capability_id else "tissue" if "tissue" in capability_id else "macro"
        capabilities.append(Capability(capability_id, status, required, tuple(x for k in present for x in by_kind[k]), reasons, (domain,)))

    coverage = {
        "macro": "available" if any(c.status == "available" and c.output_domains == ("macro",) for c in capabilities) else "unavailable",
        "tissue": "available" if any(c.status == "available" and c.output_domains == ("tissue",) for c in capabilities) else "unavailable",
        "cellular": "available" if any(c.status == "available" and c.output_domains == ("cellular",) for c in capabilities) else "unavailable",
        "molecular": "available" if any(c.status == "available" and c.output_domains == ("molecular",) for c in capabilities) else "unavailable",
    }
    limitations = [
        "Capability availability does not establish scientific or clinical validity.",
        "Missing evidence is not equivalent to a negative biological finding.",
        "Biological age and health/disease conclusions require separately validated models and reference evidence.",
    ]
    return {
        "capabilities": [c.to_dict() for c in capabilities],
        "evidence_coverage": coverage,
        "limitations": limitations,
    }
