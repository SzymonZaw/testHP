from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InputField:
    name: str
    required: bool
    accepted_kinds: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class UserInputContract:
    version: str
    fields: tuple[InputField, ...]


CONTRACT = UserInputContract(
    version="1.0",
    fields=(
        InputField(
            "hand_images",
            True,
            ("jpg", "jpeg", "png", "dng"),
            "Standardized photographs of the hand; the minimum input for macroscopic assessment.",
        ),
        InputField(
            "hand_video",
            False,
            ("mp4", "mov"),
            "Optional motion/video capture for temporal and enhanced macroscopic analysis.",
        ),
        InputField(
            "hand_3d",
            False,
            ("ply", "obj", "glb", "stl"),
            "Optional 3D/depth representation of hand geometry.",
        ),
        InputField(
            "tissue_wsi",
            False,
            ("svs", "ndpi"),
            "Optional whole-slide tissue image from a clinically/laboratory acquired specimen.",
        ),
        InputField(
            "microscopy",
            False,
            ("tif", "tiff", "ome_tiff"),
            "Optional microscopy image(s) from a defined biological specimen.",
        ),
        InputField(
            "single_cell_rna",
            False,
            ("h5ad", "h5"),
            "Optional single-cell transcriptomic assay with sample and processing metadata.",
        ),
        InputField(
            "molecular_assay",
            False,
            ("molecular_assay",),
            "Optional validated molecular assay represented by a structured application-level artifact.",
        ),
        InputField(
            "genomics",
            False,
            ("vcf", "gvcf", "bam", "cram"),
            "Optional genomic data when explicitly consented and relevant to the intended analysis.",
        ),
        InputField(
            "proteomics",
            False,
            ("mzml",),
            "Optional proteomic mass-spectrometry data with provenance metadata.",
        ),
    ),
)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


def contract_as_dict() -> dict[str, Any]:
    return {
        "version": CONTRACT.version,
        "required": [f.name for f in CONTRACT.fields if f.required],
        "optional": [f.name for f in CONTRACT.fields if not f.required],
        "fields": [
            {
                "name": f.name,
                "required": f.required,
                "accepted_kinds": list(f.accepted_kinds),
                "description": f.description,
            }
            for f in CONTRACT.fields
        ],
        "rules": {
            "public_datasets_are_reference_only": True,
            "absence_of_optional_data_is_not_a_negative_biological_finding": True,
            "clinical_interpretation_requires_validation": True,
        },
    }


def validate_input_manifest(manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return [ValidationIssue("artifacts", "artifacts must be a list")]

    required = {f.name for f in CONTRACT.fields if f.required}
    supplied = {str(a.get("kind", "")) for a in artifacts if isinstance(a, dict)}
    if not (required & supplied):
        issues.append(ValidationIssue("hand_images", "At least one supported hand image is required."))

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            issues.append(ValidationIssue(f"artifacts[{index}]", "Each artifact must be an object."))
            continue
        if not artifact.get("path"):
            issues.append(ValidationIssue(f"artifacts[{index}].path", "A source path or object identifier is required."))
        if not artifact.get("kind"):
            issues.append(ValidationIssue(f"artifacts[{index}].kind", "An artifact kind is required."))

    return issues
