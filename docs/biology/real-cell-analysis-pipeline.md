# Real Cell Analysis Pipeline

Scope: stages 1–2 of the biological pipeline. These are research/data-analysis capabilities, not clinical diagnostic claims.

## 1. Real cell segmentation

Goal: turn real microscopy into validated cell instances.

```text
REAL MICROSCOPY
       ↓
PREPROCESSING
       ↓
NUCLEI SEGMENTATION
       ↓
CELL SEGMENTATION
       ↓
CELL INSTANCES
```

### Required inputs

- Real microscopy images and, where applicable, WSI.
- Image metadata and acquisition parameters.
- Physical scale/calibration (`pixel → µm`).
- Expert annotations for nuclei/cell boundaries.
- Dataset splits that prevent leakage between related samples/subjects.
- Ground-truth and benchmark datasets.

### Pipeline components

1. Ingest and validate image metadata.
2. Preserve the original image as immutable source evidence.
3. Apply reproducible preprocessing with recorded parameters.
4. Segment nuclei.
5. Segment whole-cell boundaries where the modality supports it.
6. Separate touching/overlapping instances.
7. Generate stable instance records containing geometry, centroid, area and source coordinates.
8. Attach model/version and provenance to every result.
9. Calculate segmentation confidence and QC metrics.
10. Compare against expert annotations using predefined benchmark metrics.

### Minimum output

```text
Image
 ↓
Cell 001
Cell 002
Cell 003
...
Cell N
```

Each cell instance must remain traceable to the source image, ROI, calibration, segmentation run and model version.

### Validation gate

No claim that the system reliably finds cells should be made until performance is measured on held-out data and reviewed against expert annotations. Failed/ambiguous instances must remain representable as `Unknown` rather than being silently forced into a valid cell.

## 2. Real cell-type recognition

Goal: assign cell-type hypotheses from validated evidence.

```text
Datasets
 ↓
Expert annotations
 ↓
Morphology
 ↓
Markers
 ↓
Molecular data
 ↓
ML model
 ↓
Independent validation
```

### Required evidence layers

- Reference datasets appropriate to tissue and microscopy modality.
- Expert annotations and labeling protocol.
- Morphological features extracted from validated cell instances.
- Marker measurements where available.
- Molecular measurements where available and properly linked to spatial/cell identity.
- Explicit handling of missing modalities.

### Pipeline components

1. Define the cell-type ontology and allowed labels.
2. Build training/reference datasets with provenance.
3. Separate subject/sample-level train, validation and test sets.
4. Extract reproducible morphology features.
5. Integrate marker and molecular evidence only when linkage quality is known.
6. Train and benchmark candidate classifiers.
7. Produce `cell_type` plus confidence/uncertainty and supporting evidence.
8. Preserve alternative hypotheses where evidence is ambiguous.
9. Validate on an independent dataset and, where applicable, across sites/batches/modalities.

### Minimum output

```text
Cell 001
 ↓
cell_type: <validated label or Unknown>
 ↓
confidence / uncertainty
 ↓
evidence
 ↓
model + dataset provenance
```

### Validation gate

A cell type is an inference, not ground truth. The system must expose uncertainty, dataset limitations and out-of-distribution/unknown cases. Independent validation is required before treating classification performance as established.

## End-to-end boundary

The first biological milestone is therefore:

```text
REAL MICROSCOPY
      ↓
SEGMENTATION
      ↓
CELL ID / INSTANCE
      ↓
CELL TYPE
      ↓
CELL FEATURES
```

This document intentionally does not implement clinical health, pathology or biological-age conclusions. Those stages require their own validated biological definitions, datasets and independent validation.
