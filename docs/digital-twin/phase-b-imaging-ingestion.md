# Phase B — Imaging ingestion

The imaging boundary now explicitly supports metadata contracts for DICOM and NIfTI/NIfTI.GZ sources.

## Pipeline

```text
DICOM / NIfTI / US source
        ↓
 canonical source DataObject
        ↓
 ImagingSeries
        ↓
 source frame + geometry metadata
        ↓
 Registration
        ↓
 HAND coordinate system
        ↓
 segmentation evidence
```

## Required information

Every series is tied to `subject_id`, `hand_id` and `timepoint_id`, and references canonical source data IDs. Dimensions, voxel/pixel spacing and orientation can be retained as acquisition metadata before any registration occurs.

## Important boundary

Ingestion does **not** claim that an image is registered or segmented. A newly ingested series starts as `unregistered`. Registration must produce an explicit transform and quality/uncertainty information before the data can create a hand-space anatomical structure.

Pixel/voxel decoding and modality-specific segmentation remain separate processing stages. This keeps the data lineage auditable and prevents metadata ingestion from being mistaken for a medical interpretation.

## Privacy

The normalization helper redacts common direct-identifying DICOM-style metadata fields before they are propagated into this domain layer. Production storage must still apply the project's full privacy/security policy.
