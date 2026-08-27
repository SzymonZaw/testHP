# Phase B — Multiscale anatomy foundation

Implemented on `dev/next-cleanup`.

## Scope

Phase B establishes the domain contracts needed to connect macroscopic hand data to internal anatomy, tissue and cellular data.

```text
photo / 3d scan / MRI / US
          ↓
   hand coordinate system
          ↓
 anatomical structures
          ↓
        tissue
          ↓
   histology / microscopy
          ↓
        cells
          ↓
    cell state evidence
```

## Spatial rule

The hand coordinate system is a stable anatomical reference for a subject/hand/timepoint. Individual modalities are registered into it through explicit `Registration` objects. Visualization layers must not alter the spatial identity of evidence.

## Anatomy

`AnatomicalStructure` carries identity, geometry, source data IDs, confidence, spatial reference and provenance. Initial controlled identities include skin, fat, tendon, muscle, nerve, vessel and bone.

## Tissue

`TissueRegion` links a tissue region to its parent anatomical structure and preserves subject, hand and timepoint identity. Histology is represented by `HistologyRegion`, which links an image to the tissue region rather than existing as an anonymous slide.

## Cells

`CellObject` links a segmented/identified cell to tissue, timepoint and spatial reference. Morphology, nucleus, size, neighbors, cell type, confidence and source IDs are explicit.

## Cell state

`CellStateAssessment` is deliberately separate from the cell object. States are evidence-backed assessments, not intrinsic facts. Supported states are normal, stressed, senescent, apoptotic, proliferating, inflammatory, pathological and unknown.

## Safety of interpretation

Phase B does not implement diagnosis, biological-age calculation or treatment recommendations. Confidence and evidence are retained so later analysis can combine modalities without turning a single observation into a clinical conclusion.

## Acceptance criteria

- All modalities can reference a common hand coordinate frame.
- Registration is an explicit data object with transform, quality and uncertainty.
- Internal anatomy is linked to source observations.
- Tissue is linked to anatomy and timepoint.
- Histology is linked to tissue rather than only to a file.
- Cells are linked to tissue, spatial reference and source data.
- Cell state is an evidence-backed assessment.
- Cross-scale links preserve subject/hand/timepoint identity.
