# Photo 3D / Spatial architecture

## Canonical data flow

```text
Observation
  -> PhotoAsset
  -> PreparedPhoto
  -> RegisteredView
  -> ReconstructionAsset
  -> SpatialObject
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

## Migration rule

Stages 1-5 continue to use the existing photo manifest for persistence. The
shared spatial projection in `backend.photo_reconstruction_spatial` is the
migration boundary. Later reconstruction stages should consume that
projection and publish `ReconstructionAsset` + `SpatialObject`; they should
not create another photo/registration model.
