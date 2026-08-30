# Real spatial mapping pipeline

## Purpose

Connect real hand geometry, segmentation, tissue/cell annotations and evidence without inventing spatial relationships.

```text
real source
  -> SpatialSource
  -> SpatialAsset
  -> CoordinateSystem
  -> SpatialAnnotation
  -> validated geometryId -> regionId
  -> regionId -> evidence
  -> canonical state
  -> 3D / tree / inspector
```

## Region contract

The application recognizes these canonical region IDs:

- `palm`
- `thumb`
- `index`
- `middle`
- `ring`
- `little`
- `wrist`

A region becomes `established` only when real geometry IDs and evidence IDs are supplied and validated.

## NIH hand template

The NIH 3DPX-017237 hand template is a real anatomical registration template built from T1-weighted MR images of 27 healthy adult hands from 21 subjects. It establishes a reference hand surface, not user-specific anatomy, region segmentation, tissue geometry or cell geometry.

Therefore the adapter must not assign `palm`, `thumb`, etc. to arbitrary mesh fragments merely because their visual location appears plausible.

## Tissue/cell mapping

HuBMAP can provide real tissue/cell/spatial datasets and segmentation/coordinate information for supported specimens. Those datasets remain specimen-specific. They must be registered to the hand reference before their coordinates can be interpreted as coordinates in the Digital Twin hand.

## Registration requirement

A valid cross-dataset mapping needs:

1. source coordinate system;
2. target coordinate system;
3. transform/registration metadata;
4. provenance of the transform;
5. validation/error information;
6. explicit annotation IDs;
7. evidence links.

Without these, the UI must display `NOT ESTABLISHED` rather than creating a visual mapping.

## Personal Digital Twin

User-owned data follows the same contract:

```text
own MRI / scan / GLB / GLTF / segmentation / microscopy
  -> importer
  -> SpatialDataAdapter
  -> coordinate system
  -> annotations
  -> validation
  -> canonical state
```

The public reference assets are baselines only. They are never silently substituted for missing user data.
