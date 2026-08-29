# Multiscale data architecture v1

## Goal

The platform should accept real user evidence and produce an evidence-bounded research assessment. Public datasets are used for development, calibration and validation; they are never silently substituted for missing user evidence.

## 1. User input package

Minimum viable upload:

- subject identifier
- timepoint identifier and acquisition time
- one or more hand images
- provenance and checksum for every file

Optional evidence can be added at any scale: video, 3D, WSI/histology, microscopy, single-cell RNA, bulk RNA, genomics, proteomics, epigenetics, clinical context and explicit ground-truth labels.

The canonical schema is `data_contract/user_input_spec_v1.json`.

## 2. WSI/histology -> cells -> tissue

Pipeline contract:

`slide -> QC -> tissue region -> segmentation/annotation -> cell objects -> cell features -> spatial linkage`

Required outputs are identifiers and provenance, not a diagnosis. A cell object must retain its parent tissue region and source image/slide ID.

The repository currently has only partial support for this path. A future adapter must implement slide reading, tile generation, segmentation, QC and annotation while preserving coordinates and uncertainty.

## 3. Genomics -> biological features

Pipeline contract:

`VCF/BAM/CRAM -> QC -> normalized genomic representation -> feature extraction -> validated interpretation model`

The system must not turn variants directly into disease claims. Every interpretation requires model/version, evidence IDs and uncertainty.

Status: contract/planned.

## 4. Proteomics -> biological features

Pipeline contract:

`raw/identified proteins -> QC -> normalization -> protein/pathway features -> validated model`

Status: contract/planned. No dedicated clinical interpretation is implied.

## 5. Epigenetics -> biological features

Pipeline contract:

`methylation/chromatin signal -> QC -> normalization -> loci/region features -> validated model`

Status: contract/planned.

## 6. Biological age

There is deliberately no hard-coded biological-age number. A valid estimate requires:

- a named, versioned model
- training/validation population metadata
- compatible input modality
- model calibration information
- evidence IDs
- an uncertainty interval

Until those conditions exist, the output is `unavailable`, not an invented estimate.

The result contract is `core/biological_age.py`.

## 7. Healthy/disease ground truth

Ground truth is represented as evidence, not as a free-form assertion. Recommended label provenance:

- pathology/clinical reference standard
- clinician-confirmed diagnosis where ethically and legally appropriate
- study-provided case/control label with dataset citation
- longitudinal outcome when the endpoint is explicitly defined

Each label should retain source, cohort, target/sample ID, label definition, timestamp, annotator/reference standard and uncertainty where applicable.

A public dataset label is a validation/training label, not automatically a diagnosis for a new user.

## 8. One hand model across scales

Canonical graph:

`subject -> timepoint -> hand -> anatomical region -> tissue region -> cell -> molecular sample/feature`

Every edge needs a relation and provenance. Spatial coordinates are stored in the appropriate frame; transformations must be explicit.

This graph allows the UI to drill down from macro anatomy to tissue, cellular and molecular evidence without implying that every scale is available for every user.

## Readiness states

- `available`: implemented and testable in the repository
- `partial`: contract exists but important processing is missing
- `planned`: interface/contract only
- `contract_only`: accepted as evidence but no analytic interpretation
- `unavailable`: no evidence or validated model; return no estimate

The application must surface readiness and limitations in the result rather than silently filling gaps with reference data.
