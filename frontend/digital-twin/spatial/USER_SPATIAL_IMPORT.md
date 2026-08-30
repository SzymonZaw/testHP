# User spatial import

The application supports two spatial source classes: `reference` for external scientific geometry and `user_upload` / `own_dataset` for user-owned spatial data.

## Flow

Create a Digital Twin -> upload GLB/GLTF, STL/OBJ/PLY or future medical-image formats -> SpatialDataAdapter -> SpatialSource -> SpatialAsset -> SpatialRegion -> Canonical State -> 3D / Tree / Inspector / Evidence.

## Minimum metadata

- sourceId
- subjectId
- assetId
- format
- coordinateSystem
- provenance
- optional region mappings
- optional tissue and cell identifiers

A region mapping uses `geometryId -> regionId`. Evidence uses `regionId -> evidenceId[]`.

## Integrity rules

- User geometry is never treated as population reference geometry.
- Imported geometry does not create biological measurements.
- Missing tissue or cell segmentation stays missing.
- Evidence is linked by explicit IDs and provenance.
- Biological age, health, disease, confidence and trajectory come only from backend/model results.
- Failed or incomplete imports remain explicit error/empty states; the UI does not fabricate anatomy.

## Reference baseline

The spatial pipeline can be validated against real external sources already registered in `REFERENCE_SOURCES.md`, including NIH3D 3DPX-017237 and 3DPX-017249. These references are not substitutes for user-owned anatomy.
