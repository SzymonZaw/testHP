# User Input Protocol v1

## Purpose

This is the **end-user analysis contract**, separate from training, validation and test datasets. A user submits only the observations they actually have. The system must never interpret a missing modality as a negative finding.

## Canonical package

```text
user package
├── schema_version
├── subject
├── acquisition
├── inputs[]
└── reference
```

### `subject` — required

- `subject_id`: pseudonymous application identifier
- optional non-sensitive metadata relevant to analysis

### `acquisition` — required

- `timepoint_id`: identifier for this acquisition/session
- `acquisition_time`: ISO-8601 date-time
- `laterality`: `left`, `right`, `bilateral`, or `unknown`
- optional protocol/device metadata

### `inputs[]` — at least one required

Every input contains:

- `input_id`: unique identifier
- `kind`: supported modality
- `uri`: application-managed object reference; portable packages must not contain local machine paths
- `format`: declared file/data format
- `provenance.source_type`: `user`, `clinical`, `research_dataset`, or `derived`
- optional `region_id`, `hand_id`, `specimen_id`, `metadata`

Supported modality kinds:

`hand_images`, `hand_video`, `hand_3d`, `tissue_wsi`, `microscopy`, `single_cell_rna`, `bulk_rna`, `genomics`, `proteomics`, `epigenetics`, `clinical_context`, `ground_truth`.

## Modality-specific requirements

### `hand_images`
Required: image + laterality/session linkage. Recommended: standardized view, resolution, scale marker, camera/device, focal length, lighting and calibration metadata.

### `hand_video`
Required: video + laterality/session linkage. Recommended: frame rate, resolution, protocol/action, device and calibration.

### `hand_3d`
Required: mesh or point cloud + laterality/session linkage. Recommended: metric scale, coordinate system, scanner/device, calibration and reconstruction method.

### `tissue_wsi`
Required: WSI + tissue type + anatomical region + specimen/session linkage. Recommended: stain, scanner, magnification, pixel size, block/section and pathology annotation.

### `microscopy`
Required: microscopy object + tissue/cell context + acquisition metadata.

### `single_cell_rna`
Required: cell-level expression, cell identifiers, feature/gene identifiers and specimen linkage. Recommended: tissue/region, protocol, QC and annotations.

### `bulk_rna`
Required: expression measurements, feature/gene identifiers and sample linkage. Recommended: protocol, reference/build and QC.

### `genomics`
Required: variant/genotype representation, reference genome/build and sample linkage. Recommended: VCF/BCF-derived representation, platform and QC.

### `proteomics`
Required: protein measurements, protein/analyte identifiers and sample linkage. Recommended: assay, units, normalization and QC.

### `epigenetics`
Required: epigenetic measurements, probe/feature/region identifiers and sample linkage; reference/build where applicable. Recommended: assay, platform, normalization and QC.

### `clinical_context` / `ground_truth`
Optional. These are reference/evidence inputs, not model predictions. They may contain diagnosis, pathology labels, treatment history or independent measurements when legitimately available and appropriately governed.

## Cross-modal linkage

When multiple inputs describe the same biological object, link them explicitly:

```text
subject_id → hand_id → timepoint_id → region_id/specimen_id → input_id
```

The system must not fuse two modalities merely because they were uploaded by the same user.

## User-facing analysis response

The response must contain distinct concepts for:

1. `observed_inputs` — supplied and QC-accepted evidence
2. `available_analyses` — analyses supported by those inputs
3. `unavailable_analyses` — analyses blocked by missing/invalid evidence
4. `results` — computed outputs
5. `uncertainty` — uncertainty where supported
6. `evidence` — provenance/reference evidence
7. `limitations` — missing modalities, alignment and validation limits

The capability resolver is intentionally conservative. For example, the presence of a WSI may make tissue morphology analysis possible, but it does **not** establish a validated biological-age estimate or disease diagnosis.

## Important scientific rule

Missing evidence means **unknown / insufficient evidence**. It never means `healthy`, `diseased`, `young`, `old`, `no damage`, or `no risk`.

The current software is a research prototype. Biological-age estimation, health/disease classification and intervention prioritization require independently validated models, reference cohorts, calibration and appropriate scientific/clinical validation before clinical claims are made.
