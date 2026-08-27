# Phase C + D — Anatomy and tissue

Implemented on `dev/next-cleanup` as domain contracts and validation boundaries.

## Phase C — Anatomy

### 11. MRI / US / other sources

Imaging remains linked to canonical source data, modality, acquisition timepoint and native geometry. Import does not imply registration.

### 12. Anatomical structures

MRI/US/CT/3D segmentation produces explicit `SegmentationEvidence`; only an explicitly registered source can be promoted to an `AnatomicalStructure`.

### 13. Multimodal registration

Each modality has its native frame. `Registration` maps it into the subject/hand/timepoint `HandCoordinateSystem`, retaining transform, method, quality, uncertainty and provenance. No silent coordinate conversion is permitted.

## Phase D — Tissue

### 14. Histology

Histology is attached to a `TissueRegion`, with method, source image and spatial reference. Supported methods include H&E, immunohistochemistry and immunofluorescence.

### 15. Tissue segmentation

`TissueEvidence` binds a segmented tissue region to its parent anatomical structure, source data and spatial reference.

### 16. Tissue pathology

`TissuePathologyAssessment` is a separate evidence-backed assessment. It records findings and confidence rather than treating pathology as an intrinsic fact. Supported states include normal, atypical, inflammatory, fibrotic, degenerative, neoplastic and unknown.

## Important boundary

This phase does **not** diagnose a patient or infer treatment. It establishes traceable data structures so future validated image-analysis models can provide findings with provenance, uncertainty and confidence.

## Data lineage

```text
canonical source
      ↓
modality acquisition
      ↓
native image geometry
      ↓
explicit multimodal registration
      ↓
anatomical structure
      ↓
tissue segmentation
      ↓
histology / microscopy
      ↓
tissue pathology evidence
```

A downstream result must retain enough identifiers to trace it back to the source acquisition and timepoint.
