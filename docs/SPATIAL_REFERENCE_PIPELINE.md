# Real spatial asset pipeline

## Purpose

The Digital Twin now has an explicit boundary between public reference data and user-owned data.

```text
Reference source / User upload
            ↓
       SpatialAsset
            ↓
 geometryId → regionId
            ↓
       canonical state
            ↓
  Tree ↔ 3D ↔ Inspector ↔ Evidence
```

## Reference assets

The first reference is the NIH 3D healthy adult human hand template:

- https://3d.nih.gov/entries/3DPX-017237
- derived from T1-weighted MRI of 27 healthy adult hands from 21 subjects
- reference/template only; it is not a user's hand
- the source entry provides downloadable 3D files; the repository does not copy the external binary asset

A second reference is the NIH segmented hand/wrist bone model:

- https://3d.nih.gov/entries/3DPX-017249
- reference bone geometry only

Other research references remain catalogued in `spatial-reference-registry.js` and are not automatically registered as user observations.

## User-owned assets

The adapter accepts `.glb` and `.gltf` files after explicit user import. Metadata must identify:

- asset ID
- coordinate system
- source type
- provenance/source URL where applicable
- optional license
- explicit geometry-to-region mapping

No region is inferred from a mesh name unless the importer explicitly maps it.

## Region contract

Supported top-level regions:

`palm`, `thumb`, `index`, `middle`, `ring`, `little`, `wrist`.

The contract is deliberately extensible for future `tissueId` and `cellId` mappings.

## Three.js picking

`spatial-viewport-integration.js` walks the picked object's parent chain and looks for `geometryId`/`geometry_id`/mesh name mappings supplied by the asset. A successful pick emits `testhp:spatial-target-changed` and `testhp:spatial-layer-changed` and updates the existing spatial state bridge.

The integration never creates health, age, disease, confidence, trajectory, or treatment recommendations.

## What is intentionally not claimed

The NIH template does **not** provide patient-specific region segmentation, tissue geometry, or cell geometry. The app must therefore show `NOT ESTABLISHED` / unavailable states until those data are actually supplied.
