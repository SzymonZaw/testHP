# Photo 3D / Spatial architecture

## Canonical data flow

```text
Observation
  -> PhotoAsset
  -> PreparedPhoto
  -> RegisteredView
  -> ReconstructionAsset
  -> SpatialObject
  -> Spatial Model / Inspector / Navigation / Research Interpretation
```

A photo is evidence. A prepared photo is a processed representation. A
registered view is a prepared photo with a hand-space registration. A
reconstruction is a versioned result. A SpatialObject is the shared spatial
entity consumed by the Spatial Model, Inspector, Navigation and Research
Interpretation.

## Ownership

| Module | Owns | Does not own |
|---|---|---|
| Hand Surface | segmentation, landmarks, hand coordinates, surface evidence | mesh reconstruction |
| Photo 3D Reconstruction | multi-view registration orchestration, geometry/texture reconstruction | global spatial identity |
| Spatial Model | SpatialObject lifecycle and spatial relationships | photo preparation |
| Spatial Inspector | presentation of selected SpatialObject | reconstruction algorithms |
| Spatial Navigation | camera, selection, focus and navigation state | object provenance |
| Research Interpretation | interpretation, observations, confidence and provenance | rendering |

## Identity rules

The following IDs are intentionally different and composable:

- `observation:<photo-id>` — source observation
- `photo:<asset-id>` — source photo asset
- `prepared-photo:<asset-id>` — prepared representation
- `registered-view:<prepared-photo-id>:<view>` — registered view
- `reconstruction:<subject>:<timepoint>:<nonce>` — reconstruction result
- `spatial-hand:<subject>:<reconstruction-id>` — spatial entity

The same physical photo must not receive a second independent identity in
another module. Downstream modules consume the shared IDs instead.

## Lifecycle

```text
created -> prepared -> registered -> reconstructed -> published
                         |              |
                         +-> needs_review
                                        +-> failed
```

Legacy stage-specific statuses are translated at the boundary by
`backend.spatial_contract.lifecycle()`.

## Stages 6-10 boundary

The reconstruction orchestrator is the single write boundary for the 3D
result. It validates registered views, builds the silhouette-envelope mesh,
generates a multi-view reference texture atlas, then publishes one
`ReconstructionAsset` and one `SpatialObject`.

Persistent outputs are grouped under one reconstruction directory:

- `manifest.json` — compatibility manifest
- `reconstruction.json` — canonical reconstruction record
- `hand.obj` / `hand.mtl` — geometry asset
- `texture.png` — multi-view reference atlas when raster inputs are available

The canonical SpatialObject index is stored at
`data/registry/spatial_objects.json` and is exposed through
`/api/spatial/objects`.

The current geometry method is `silhouette-envelope-v1` because calibrated
camera intrinsics/extrinsics are not yet part of the registration contract.
The texture stage therefore creates a provenance-preserving reference atlas,
not a claim of calibrated surface projection. A future calibrated projection
worker can replace that implementation without changing the SpatialObject or
ReconstructionAsset identity.

## Migration rule

Stages 1-5 continue to use the existing photo manifest for source persistence.
The shared spatial projection in `backend.photo_reconstruction_spatial` is the
input boundary. Stages 6-10 consume the registered records and publish
`ReconstructionAsset` + `SpatialObject`; they do not create another photo or
registration model.
