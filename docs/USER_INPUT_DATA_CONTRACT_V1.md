# User Input Data Contract v1

Status: **research/prototype contract**

This document defines the smallest honest set of inputs that a future user-facing Hand Digital Twin can accept. Missing modalities are allowed. The system must never fabricate evidence or silently promote a parent-level observation to a deeper level.

## 1. Identity and acquisition metadata

Every upload is attached to a subject and timepoint and carries provenance.

Required:

- `subject_id`
- `timepoint_id`
- `modality`
- `source_file`
- `acquisition_time` (or explicit `unknown`)
- `body_site = hand`
- `hand_side = left | right | bilateral | unknown`

Recommended:

- age at acquisition, if available
- sex, if scientifically justified and permitted by the use case
- device/instrument
- protocol identifier
- operator/site
- calibration metadata
- consent/usage metadata
- file checksum

## 2. Hand surface / macro imaging

### Minimum viable input

One hand, one side, a standardized set of photographs:

- dorsal
- palmar
- radial side
- ulnar side
- thumb-oriented view

Each image should include either a calibrated scale/marker or a documented acquisition geometry. Images without scale remain usable as qualitative evidence but must be marked `metric_geometry=false`.

Recommended capture:

- fixed camera distance
- fixed focal length/zoom
- diffuse, stable illumination
- neutral background
- complete hand visible
- no occluding objects
- left/right explicitly recorded
- RAW or lossless/high-quality image preferred

### Optional

- short calibrated video
- multi-view image set
- depth map
- RGB-D
- photogrammetry/structured-light 3D
- mesh + texture

### Output contract

`hand_images` -> quality assessment -> landmarks/segmentation -> normalized hand geometry -> anatomical regions.

`hand_3d` -> calibration/registration -> surface mesh/point cloud -> anatomical coordinate frame -> region geometry.

## 3. WSI / histology

Accepted evidence should describe both the specimen and the tissue context.

Required when WSI is supplied:

- whole-slide image or supported microscopy image
- stain/protocol if known
- tissue/sample identifier
- anatomical site
- magnification or physical pixel size when available
- acquisition metadata when available

Pipeline:

```text
WSI
 -> tissue/background QC
 -> tissue region segmentation
 -> cell/nucleus segmentation
 -> cell instance table
 -> cell type / phenotype inference
 -> cell coordinates in slide coordinates
 -> neighborhood / microenvironment graph
 -> tissue architecture
 -> registration to anatomical hand region when defensible
```

A cell-level result is only considered spatially linked to the hand when a valid registration chain exists.

## 4. Genomics

The contract accepts either raw or processed genomic evidence, but the processing level must be explicit.

Preferred inputs:

- VCF/BCF or equivalent variant representation
- aligned sequence data when processing is performed by the platform
- gene-level/variant-level annotations

Pipeline:

```text
genomic evidence
 -> QC / normalization
 -> variants and/or genomic features
 -> annotation
 -> functional interpretation
 -> biological features
 -> model input
```

The platform must preserve genome build, assay, processing pipeline and annotation version.

## 5. Transcriptomics

RNA evidence is distinct from genomics.

Accepted forms:

- single-cell RNA-seq
- spatial transcriptomics
- bulk RNA-seq
- processed expression matrix

Required metadata:

- assay type
- gene identifier namespace
- sample/tissue identity
- processing state
- reference genome/annotation when applicable

Pipeline:

```text
RNA evidence
 -> QC / normalization
 -> expression features
 -> cell type / tissue context
 -> pathway/state features
 -> biological state model
```

## 6. Proteomics

Preferred inputs:

- quantified protein abundance table
- peptide-level evidence when available
- raw mass-spectrometry data for a future processing tier

Required metadata:

- assay/platform
- sample/tissue
- units
- normalization state
- protein identifier namespace

Pipeline:

```text
proteomic evidence
 -> QC / normalization
 -> protein features
 -> pathways / protein complexes
 -> cell/tissue state features
 -> biological state model
```

## 7. Epigenetics

The contract supports multiple epigenetic assays, but they must not be collapsed into one generic value.

Accepted classes:

- DNA methylation
- chromatin accessibility
- histone modifications
- other explicitly identified epigenetic assays

Required metadata:

- assay type
- genome build/reference
- feature namespace
- processing state
- sample/tissue identity

Pipeline:

```text
epigenetic evidence
 -> QC / normalization
 -> assay-specific features
 -> biological/epigenetic features
 -> validated age/state model where available
```

## 8. Clinical/pathology reference labels

For supervised health/disease evaluation, the platform needs a reference label with provenance.

Examples:

- healthy/reference
- disease category
- histopathology diagnosis
- subtype
- severity/stage where clinically defined

Each label must record:

- label value
- label source
- assessor or source dataset
- assessment date/time when available
- evidence/sample linkage
- confidence or adjudication status

A model prediction is **not** a ground-truth label.

## 9. Biological age

The platform must separate chronological age from biological-age estimates.

For every estimate store:

- target level: `cell | tissue | region | hand`
- estimated age
- uncertainty interval or equivalent uncertainty representation
- model identifier/version
- training/reference population
- input modalities actually used
- applicability/domain-of-validity metadata

No biological-age number should be emitted as a validated clinical fact unless the underlying model has appropriate external validation.

## 10. Missingness rules

The user does **not** need to provide every modality.

The result must explicitly state evidence availability:

```text
hand imaging       available / missing
3D                 available / missing
histology          available / missing
transcriptomics    available / missing
genomics           available / missing
proteomics         available / missing
epigenetics        available / missing
reference labels   available / missing
```

Missing evidence means `unknown`, not `healthy`, `normal`, or `zero risk`.

## 11. Evidence hierarchy

Every derived result must carry:

```text
evidence_ids
source_data_ids
processing_pipeline
model_id/model_version
provenance
uncertainty
spatial_level
timepoint
```

Derived outputs must never lose the link to their source observations.

## 12. User-facing minimum package

The first practical product should accept:

```text
A. Standardized hand photographs
B. Optional calibrated 3D/depth data
C. Optional pathology/WSI
D. Optional molecular data (RNA, genomic, proteomic, epigenetic)
E. Optional clinical/reference labels
```

The system then returns only the analyses supported by the supplied evidence. It should be possible to run a macro-only assessment without pretending that cellular or molecular information exists.

## 13. Product boundary

This contract describes a research evidence pipeline. It does not establish clinical validity, diagnosis, treatment recommendations, rejuvenation decisions, or a demonstrated ability to support extreme longevity claims. Those require separate scientific validation and regulatory work.
