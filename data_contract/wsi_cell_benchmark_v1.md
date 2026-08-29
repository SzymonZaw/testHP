# WSI cell benchmark contract v1

## Purpose

This contract separates three different tasks that must not be conflated:

1. **nuclei/cell detection and segmentation** from H&E images;
2. **cell-type classification** from morphology or multimodal evidence;
3. **skin-specific validation** for an end-user hand/skin WSI.

A dataset can be useful for (1) without being valid ground truth for (2) or (3).

## Public benchmark candidates

### MoNuSAC 2020

- Scope: H&E nuclei segmentation and classification across multiple organs.
- Use in this project: technical benchmark for nuclei detection/instance segmentation and a general cell/nucleus classification baseline.
- Repository/code reference: https://github.com/BethaniaCandra/Multi-Organ-Nuclei-Segmentation-and-Classification-Challenge-MoNuSAC-2020-
- Important limitation: it is **not a skin-specific benchmark** and therefore must not be used alone to claim validated skin cell-type inference.

### PanNuke

- Scope: large multi-tissue nuclei segmentation/classification resource.
- Use in this project: pretraining/robustness benchmark for nuclei segmentation and morphology across tissue types.
- Important limitation: cross-tissue data are not a substitute for skin-specific validation or hand-specific ground truth.

## Skin-specific validation requirement

The end-user WSI classifier must not be marked `validated` until the project has an image/spatial dataset satisfying all of the following:

- human skin tissue;
- H&E or another explicitly supported histology modality;
- image/tile or WSI coordinates;
- cell/nucleus instance annotations;
- cell-type labels or a defensible annotation protocol;
- subject/donor identifiers;
- enough independent donors for held-out evaluation;
- licence permitting the intended research use;
- documented annotation provenance.

A scRNA-seq skin atlas such as HSCA can provide an independent label vocabulary and biological reference, but it is **not** image ground truth for H&E morphology.

## Validation levels

The pipeline must expose one of these states:

- `technical_benchmark_only`: tested on generic histology datasets;
- `skin_reference_supported`: labels can be cross-checked against skin molecular references, but image classification is not validated;
- `skin_image_validated`: independent skin histology data with cell-level annotations have been used for held-out evaluation;
- `hand_specific_validated`: independent hand-tissue data have been used for held-out evaluation.

Until the corresponding evidence exists, end-user cell-type results must carry `validated_domain=false`.

## Required benchmark record

Each benchmark record should preserve:

- dataset_id;
- source_url;
- tissue;
- modality;
- annotation_level;
- cell_types;
- donor/sample split;
- licence;
- task;
- validation_level;
- provenance.

## Current project decision

The repository currently has enough public resources to benchmark the **technical segmentation layer**, but does not yet have a verified public skin H&E/WSI cell-type dataset that should be treated as the project's final ground truth.

Therefore the next implementation stage must build an evaluation adapter and keep skin cell-type inference in `not_established` until a qualifying skin image dataset is imported and evaluated.
