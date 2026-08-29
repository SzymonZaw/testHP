from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Artifact:
    """One user-supplied artifact; no clinical meaning is inferred from it."""

    kind: str
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Capability:
    level: str
    available: bool
    missing: tuple[str, ...]
    reason: str


# These are intentionally conservative. They describe what can be attempted,
# not what a model is clinically validated to conclude.
CAPABILITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "macro": ("hand_images",),
    "macro_enhanced": ("hand_images",),
    "tissue": ("tissue_wsi",),
    "cellular": ("microscopy", "single_cell_rna"),
    "molecular": ("molecular_assay",),
}


KIND_ALIASES = {
    "jpg": "hand_images",
    "jpeg": "hand_images",
    "png": "hand_images",
    "dng": "hand_images",
    "tiff": "hand_images",
    "tif": "microscopy",
    "svs": "tissue_wsi",
    "ndpi": "tissue_wsi",
    "ome_tiff": "microscopy",
    "h5ad": "single_cell_rna",
    "h5": "single_cell_rna",
    "mp4": "hand_video",
    "mov": "hand_video",
    "ply": "hand_3d",
    "obj": "hand_3d",
    "glb": "hand_3d",
    "stl": "hand_3d",
    "vcf": "genomics",
    "gvcf": "genomics",
    "bam": "genomics",
    "cram": "genomics",
    "mzml": "proteomics",
}


def normalize_kind(kind: str) -> str:
    return KIND_ALIASES.get(kind.lower().lstrip("."), kind.lower())


def available_modalities(artifacts: list[Artifact]) -> set[str]:
    return {normalize_kind(a.kind) for a in artifacts}


def _has_any(modalities: set[str], alternatives: tuple[str, ...]) -> bool:
    return any(item in modalities for item in alternatives)


def assess_capabilities(artifacts: list[Artifact]) -> list[Capability]:
    modalities = available_modalities(artifacts)
    capabilities: list[Capability] = []

    macro_ok = "hand_images" in modalities
    capabilities.append(
        Capability(
            "macro",
            macro_ok,
            () if macro_ok else ("hand_images",),
            "At least one hand image is required for the macro baseline.",
        )
    )

    enhanced_ok = macro_ok and ("hand_video" in modalities or "hand_3d" in modalities)
    capabilities.append(
        Capability(
            "macro_enhanced",
            enhanced_ok,
            () if enhanced_ok else tuple(
                x for x in ("hand_images", "hand_video_or_3d")
                if x == "hand_images" and not macro_ok or x == "hand_video_or_3d" and not ("hand_video" in modalities or "hand_3d" in modalities)
            ),
            "Enhanced macro analysis requires images plus video or 3D/depth data.",
        )
    )

    tissue_ok = "tissue_wsi" in modalities
    capabilities.append(
        Capability(
            "tissue",
            tissue_ok,
            () if tissue_ok else ("tissue_wsi",),
            "Tissue morphology requires tissue imaging; it cannot be inferred from a photograph of the hand.",
        )
    )

    cellular_ok = _has_any(modalities, ("microscopy", "single_cell_rna"))
    capabilities.append(
        Capability(
            "cellular",
            cellular_ok,
            () if cellular_ok else ("microscopy_or_single_cell_rna",),
            "Cellular analysis requires microscopy or a single-cell assay.",
        )
    )

    molecular_ok = any(
        item in modalities for item in ("molecular_assay", "single_cell_rna", "genomics", "proteomics")
    )
    capabilities.append(
        Capability(
            "molecular",
            molecular_ok,
            () if molecular_ok else ("molecular_assay",),
            "Molecular analysis requires an appropriate molecular assay.",
        )
    )

    return capabilities


def build_capability_report(artifacts: list[Artifact]) -> dict[str, Any]:
    capabilities = assess_capabilities(artifacts)
    return {
        "available_modalities": sorted(available_modalities(artifacts)),
        "capabilities": [
            {
                "level": item.level,
                "available": item.available,
                "missing": list(item.missing),
                "reason": item.reason,
            }
            for item in capabilities
        ],
        "policy": {
            "missing_data_is_not_normal": True,
            "public_datasets_are_reference_only": True,
            "clinical_or_biological_conclusions_require_validated_models": True,
        },
    }
