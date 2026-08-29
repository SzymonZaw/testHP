from __future__ import annotations

"""Additional external tools/models available to testHP.

These entries intentionally keep external weights and heavy dependencies out
of the repository. They describe capabilities and let the benchmark layer
select among interchangeable implementations.
"""

from .model_registry import ModelSpec


ADDITIONAL_MODEL_REGISTRY: dict[str, ModelSpec] = {
    "scfoundation": ModelSpec(
        "scfoundation", "scFoundation", "foundation_model",
        "single-cell representation and perturbation modelling",
        "https://github.com/biomap-research/scFoundation",
        "code is Apache-2.0; verify upstream terms for model weights",
        ("single-cell expression",),
        ("cell embeddings", "cell representations", "perturbation outputs"),
        tags=("single-cell", "foundation-model", "perturbation"),
    ),
    "scvi-tools": ModelSpec(
        "scvi-tools", "scvi-tools", "analysis_tool",
        "probabilistic single-cell integration and latent modelling",
        "https://github.com/scverse/scvi-tools",
        "BSD-3-Clause; verify individual model/data terms",
        ("single-cell expression",),
        ("latent representations", "integrated datasets", "uncertainty-aware results"),
        optional_dependency="scvi",
        tags=("single-cell", "probabilistic", "integration", "uncertainty"),
    ),
    "deepcell-mesmer": ModelSpec(
        "deepcell-mesmer", "DeepCell / Mesmer", "image_model",
        "whole-cell and nuclear segmentation",
        "https://github.com/vanvalenlab/deepcell-tf",
        "verify upstream repository/license for the selected release and weights",
        ("microscopy image",), ("cell masks", "nuclear masks"),
        optional_dependency="deepcell",
        tags=("segmentation", "microscopy", "multiplex"),
    ),
    "cellsam": ModelSpec(
        "cellsam", "CellSAM", "image_model", "general cell segmentation",
        "https://github.com/vanvalenlab/cellSAM",
        "verify upstream repository/license and weights terms",
        ("microscopy image",), ("cell masks",),
        tags=("segmentation", "microscopy", "foundation-model"),
    ),
    "stardist": ModelSpec(
        "stardist", "StarDist", "image_model", "2D/3D nucleus and cell segmentation",
        "https://github.com/stardist/stardist",
        "verify upstream repository/license and pretrained-model terms",
        ("2D/3D microscopy",), ("instance labels",),
        optional_dependency="stardist",
        tags=("segmentation", "microscopy", "3d", "nuclei"),
    ),
    "qupath": ModelSpec(
        "qupath", "QuPath", "analysis_tool", "digital pathology image analysis and annotations",
        "https://github.com/qupath/qupath",
        "verify upstream project license and bundled model licenses",
        ("WSI/tissue image",), ("regions", "annotations", "cell measurements"),
        tags=("pathology", "wsi", "analysis"),
    ),
    "monai": ModelSpec(
        "monai", "MONAI", "analysis_tool", "medical imaging AI and segmentation infrastructure",
        "https://github.com/Project-MONAI/MONAI",
        "Apache-2.0; verify individual model/data terms",
        ("medical image",), ("model inference", "segmentations", "embeddings"),
        optional_dependency="monai",
        tags=("medical-imaging", "segmentation", "deep-learning"),
    ),
    "nicheformer": ModelSpec(
        "nicheformer", "Nicheformer", "foundation_model", "spatial cellular niche representation",
        "https://github.com/theislab/nicheformer",
        "verify upstream repository/license and weights terms",
        ("spatial transcriptomics",), ("niche embeddings", "cell representations"),
        tags=("spatial", "foundation-model", "niche"),
    ),
    "deepspot-m": ModelSpec(
        "deepspot-m", "DeepSpot-M", "foundation_model", "histology-to-spatial molecular prediction",
        "https://www.medrxiv.org/",
        "research/preprint implementation; verify implementation and terms before production use",
        ("histology image",), ("predicted spatial molecular features",),
        tags=("spatial", "pathology", "experimental"),
    ),
    "virtues": ModelSpec(
        "virtues", "VirTues / Virtual Tissues", "foundation_model",
        "spatial proteomics and cellular niche modelling",
        "https://www.nature.com/",
        "verify publication implementation, weights, and data terms before use",
        ("spatial proteomics",), ("cell representations", "niche annotations", "spatial biomarkers"),
        tags=("spatial", "proteomics", "experimental"),
    ),
}
