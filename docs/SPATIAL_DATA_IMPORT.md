# Spatial data: real hand / tissue / cell inputs

The Digital Twin must distinguish **real spatial evidence** from UI placeholders. This contract lets a user bring their own `.glb`/`.gltf` asset and metadata without inventing anatomy or biological results.

## 1. Source → asset → annotation

```text
SpatialSource
   ↓
SpatialAsset (.glb/.gltf)
   ↓
SpatialRegion / SpatialAnnotation
   ↓
canonical state
   ↓
evidence
```

The browser-side implementation is `frontend/digital-twin/spatial-data-model.js` and exposes `window.testhpSpatialDataModel`.

## 2. Minimal manifest

```json
{
  "spatialSource": {
    "id": "my-hand-scan-001",
    "type": "user_upload",
    "label": "My hand 3D scan",
    "uri": "https://example.org/my-hand.glb",
    "license": "CC-BY-4.0",
    "provenance": {
      "capturedAt": "2026-08-30T12:00:00Z",
      "method": "3d_scan"
    }
  },
  "spatialAsset": {
    "id": "hand-asset-001",
    "uri": "https://example.org/my-hand.glb",
    "format": "glb",
    "coordinateSystem": {
      "id": "scanner-world",
      "units": "mm",
      "handedness": "right",
      "origin": [0, 0, 0],
      "axes": { "x": "right", "y": "up", "z": "forward" }
    },
    "regions": [
      { "geometryId": "mesh_palm", "regionId": "palm", "evidenceIds": [{ "id": "scan-001", "source": "my-hand-scan-001" }] },
      { "geometryId": "mesh_thumb", "regionId": "thumb", "evidenceIds": [{ "id": "scan-001", "source": "my-hand-scan-001" }] },
      { "geometryId": "mesh_index", "regionId": "index", "evidenceIds": [{ "id": "scan-001", "source": "my-hand-scan-001" }] }
    ]
  },
  "annotations": [
    {
      "id": "cell-or-landmark-001",
      "type": "point",
      "coordinateSystem": { "id": "scanner-world", "units": "mm", "handedness": "right" },
      "coordinates": [12.1, 44.2, 7.3],
      "regionId": "palm",
      "tissueId": null,
      "cellId": null,
      "sourceId": "my-hand-scan-001"
    }
  ]
}
```

## 3. Required region IDs

The canonical region vocabulary is:

- `palm`
- `thumb`
- `index`
- `middle`
- `ring`
- `little`
- `wrist`

The validator rejects unknown or duplicate region IDs and requires every mapped region to have a `geometryId`.

## 4. User-owned data

The application should accept a user's own asset and metadata. The asset itself does **not** become biological truth merely because it was uploaded. Provenance, acquisition method, coordinate system, license and evidence links remain attached to it.

For clinical or research use, the user should also retain the original source data and acquisition metadata outside the frontend.

## 5. Tissue and cell extensions

The same manifest can later add:

```text
regionId → tissueId → cellId → annotation/geometry
```

For cells, the spatial annotation should carry a real coordinate system and a source-backed cell identifier. A frontend-generated `Cell A17` is not valid evidence.

## 6. External reference datasets

External public datasets can be registered as `SpatialSource` references instead of being copied into the repository. The reference must record the dataset's stable identifier/URL, license, version/access date and the exact mapping used.

Suitable public resources should be added only after checking that their licensing, anatomy, spatial resolution and metadata support the intended use. A reference to a dataset is not the same as having a subject-specific twin.

## 7. Safety / scientific rule

Spatial data can establish **where a measured object is**. It does not by itself establish health, disease, biological age, confidence, trajectory or treatment. Those results remain backend/model outputs and must stay `NOT ESTABLISHED` when no validated source exists.
