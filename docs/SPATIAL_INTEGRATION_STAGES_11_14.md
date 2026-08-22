# Spatial integration — stages 11-14

## 11. Provenance and lifecycle

Every reconstruction records source photo IDs, prepared-photo IDs, registered-view IDs, method, version, quality and creation time. Lifecycle transitions are centralized in `backend.spatial_provenance`.

## 12. UX

PHOTO 3D presents reconstruction as one spatial object. Technical provenance remains available as metadata rather than being required for the primary build flow. The shared inspector adapter consumes `SpatialObject` directly.

## 13. Module integration

- Spatial Model owns the spatial entity.
- Inspector renders the selected `SpatialObject`.
- Navigation owns selection/focus events.
- Photo 3D owns reconstruction production.
- Hand Surface remains the source of prepared/registered hand evidence.

No module should create a second identity for the same spatial object.

## 14. Regression contract

The integration boundary is intentionally small: `SpatialObject`, `ReconstructionAsset`, lifecycle/provenance helpers, and navigation selection/focus events. Existing Hand Surface and Photo 3D manifests remain compatible while consumers migrate to the shared contracts.
