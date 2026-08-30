# Real spatial reference test

This test uses public anatomical references instead of inventing a hand geometry.

## Primary reference

NIH 3D 3DPX-017237 — 3D Model of an Anatomical Template of Healthy Adult Human Hand:
https://3d.nih.gov/entries/3DPX-017237

The model is a population-derived anatomical template created from T1-weighted MRI of 27 healthy adult hands. It is a reference model, not an individual's Digital Twin.

## Secondary reference

NIH 3D 3DPX-017249 — Bones of the Healthy Adult Human Hand/Wrist:
https://3d.nih.gov/entries/17249

This is a segmented bone model and is useful for validating spatial loading/picking, but it does not provide complete soft-tissue or cellular geometry.

## Integration rule

Do not silently download or vendor external medical assets. The application should keep a reference to the source and let the user import a permitted local `.glb`/`.gltf` asset when a browser-ready file is needed.

For an imported asset, every selectable mesh should carry metadata such as:

```json
{
  "geometryId": "hand-palm-001",
  "regionId": "palm",
  "tissueId": null,
  "cellId": null,
  "sourceId": "nih3d-3dpx-017237"
}
```

The picker must resolve only explicit metadata. If `regionId`/`tissueId`/`cellId` is absent, the UI must not infer it from mesh position or display name.

## Acceptance test

1. Import the downloaded/converted reference asset locally.
2. Attach explicit geometry metadata to the meshes that are intended to be selectable.
3. Load the asset in the Digital Twin viewport.
4. Click a mesh.
5. Verify the resolved `geometryId` and `regionId` enter canonical state.
6. Verify Tree, 3D highlight, Inspector and Evidence receive the same identity.
7. Verify an unmapped mesh produces no biological selection.
8. Record the source URL, asset version/hash and any conversion step in provenance.

## Important limitation

This reference can validate the spatial pipeline and anatomical visualization. It does **not** provide tissue segmentation, single-cell geometry, cell IDs, or cell-level molecular measurements. Those require additional datasets or the user's own imaging/segmentation data.
