# Images modality audit — Stage 9

## Role

`data/raw/images/` is the macroscopic skin-imaging layer. It should contain ordinary-camera or otherwise non-microscopic skin observations and metadata associated with them. It is a reference/training layer for the system, not automatically a source of diagnoses for a personal subject.

## Current repository structure

The current tree contains four conceptual groups: `aging_skin/`, `lesions/`, `normal_skin/` and `pathology/scin/`. citeturn147file0turn156file0

### `aging_skin/`

Current files: three JPEG images plus `info.txt`. The info file explicitly says `Własne zdjęcia` (own photographs). citeturn153file0turn162file0

**Role:** personal/reference macroscopic skin observations intended to represent ageing-related appearance. Because these files are personal images, they should be kept separate from external labelled datasets in future metadata.

### `normal_skin/`

Current files: three JPEG images plus `Info.txt`. The three JPEGs have exactly the same Git object SHAs as the three files in `aging_skin/`. The metadata also says the content is similar to `lesions/skin_lesions_dataset`. citeturn155file0turn163file0

**Audit finding:** this directory currently cannot be treated as an independent normal-skin reference set. The duplicate file content must be resolved before using it for reference comparisons or model evaluation.

### `lesions/`

Contains `ISIC/` and `skin_lesions_dataset/`. citeturn154file0

**Role:** external/reference skin-lesion imagery. It can support development of lesion-oriented image analysis, but dataset labels must remain provenance metadata and must not be interpreted as ground truth for a new personal image without a validated task and model.

### `pathology/scin/`

The current repository contains a `scin/` directory under `pathology`. citeturn156file0

**Audit finding:** the folder name is scientifically ambiguous. SCIN should be treated as a skin-condition/clinical-image source until its exact contents and labels are verified. It should not be assumed to contain histopathology or microscopy merely because it sits under `pathology/`.

A later cleanup should consider a structure such as `images/conditions/scin/` or `images/lesions/scin/` if that matches the verified dataset semantics.

## Information map for images

### Acquisition level

- file readability;
- file format;
- dimensions;
- colour channels;
- file size;
- metadata where available;
- duplicate detection;
- provenance and dataset identity.

### Macroscopic visual level

- skin/region detection;
- colour statistics;
- brightness and exposure;
- texture descriptors;
- visible surface patterns;
- geometry and area of a visible lesion/region;
- border/shape descriptors when segmentation is validated.

### Spatial level

- image coordinate system;
- region of interest;
- lesion location within the image;
- correspondence to an explicit anatomical location when metadata supports it.

### Temporal level

Only when repeated observations belong to the same explicit subject and acquisition is sufficiently comparable:

- change in measured colour/texture/area;
- change rate;
- persistence/disappearance;
- change-point candidates.

### Interpretation boundary

The image layer may produce descriptive observations and validated visual features. It must not infer cancer, disease risk, biological age or cellular age from ordinary RGB images alone.

## Stage 9 decision

`images/` is therefore defined as the **macroscopic skin observation and reference layer**. Its first engineering target should be robust descriptive measurements, provenance separation and spatial ROI support. Disease/ageing interpretation comes later and requires validated modality-specific models.
