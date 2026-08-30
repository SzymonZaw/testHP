# Spatial data contract

The spatial layer is an adapter boundary between backend-owned spatial data and the Digital Twin UI.

## Sources

`SpatialSource` identifies where a spatial asset came from. Supported source classes are `own_scan`, `own_dataset`, `research_dataset`, `reference_model`, and `reconstructed`.

## Assets

`SpatialAsset` references a `.glb`/`.gltf` asset, a coordinate-system ID, and a set of spatial regions. The frontend must not create biological geometry when the backend has not supplied it.

## Regions

Canonical region IDs are:

- `palm`
- `thumb`
- `index`
- `middle`
- `ring`
- `little`
- `wrist`

Every supplied region maps `geometryId -> regionId`. The region ID is stable and independent of its display label.

## Coordinate system

Every asset declares a `coordinateSystemId`. The manifest must provide units, origin, axis semantics, and handedness when those facts are known. Unknown values remain unknown; they are not inferred by the UI.

## Annotations

Spatial annotations may represent landmarks/points, masks, segmentations, tissue IDs, or cell IDs. Tissue and cell fields are optional so a region-only asset remains valid.

## Evidence

Evidence references can be scoped to `subjectId`, `timepointId`, `regionId`, `tissueId`, and `cellId`. This allows the UI to answer which evidence supports a selected spatial object without treating evidence coverage as biological confidence.

## Own-data import

The browser importer accepts `.glb` and `.gltf` files plus a metadata object and region manifest. A GLTFLoader-compatible loader is injected by the application. The importer validates source, coordinate system, region IDs, and geometry IDs before loading the asset.

## Canonical state

Spatial selection updates only `region`, `tissue`, and `cell` in the existing Digital Twin canonical state. Higher-level biological results remain backend-owned.

## 3D interaction

The Three.js helper uses `Raycaster` and `userData.spatial` metadata. A mesh can carry:

```text
geometryId
regionId
tissueId
cellId
```

Picking resolves the most specific supplied object and sends its stable ID back to the canonical state.
