# Hand Surface Layer State · Stage 3

`window.handSurfaceLayerState` is the canonical frontend boundary for the hand-surface state. Existing UI/renderer modules remain in place, but new integrations should read and write this contract instead of reaching directly into another module's private state.

## Shape

```text
HandSurfaceState
├── version
├── mode: classic | real
├── subject_id
├── timepoint
├── target
│   ├── spatial_id
│   └── label
├── layer
│   ├── geometry
│   │   ├── source: real | derived | default | none
│   │   ├── status: missing | partial | ready | error
│   │   └── data
│   ├── measurements
│   │   ├── source
│   │   ├── status
│   │   └── data
│   ├── images[]
│   │   ├── asset_id
│   │   ├── evidence_id
│   │   ├── view
│   │   ├── spatial_id
│   │   ├── prepared
│   │   ├── registered
│   │   └── projection
│   ├── observations[]
│   └── projection
│       ├── source
│       ├── status
│       └── data
├── readiness
└── effective
```

## Rules

1. `target.spatial_id` is the spatial identity. Changing depth changes the target; it must not implicitly rewrite image ownership.
2. `source` describes provenance. `status` describes availability. They are separate dimensions.
3. `effective` is derived state: it answers which source is currently usable for each data category.
4. `real_hand` readiness is not the same as "the real mode button was clicked".
5. Missing data is represented explicitly; consumers should hide controls that have no usable data rather than render empty controls.
6. Images are identified by stable `asset_id` and may independently progress through preparation, registration and projection.
7. The store is compatible with the existing events and local-storage measurements so the migration can be incremental.

## API

- `snapshot()` — immutable copy of the complete state.
- `getLayer()` — current layer state.
- `getTarget()` / `setTarget(target)` — spatial target boundary.
- `getMode()` / `setMode(mode)` — classic/real mode.
- `setGeometry(data, {source, status})` — geometry state.
- `setMeasurements(data, {source, status})` — measurement state.
- `upsertImage(image)` / `removeImage(assetId)` — image state.
- `setProjection(data, {source, status})` — projection state.
- `setObservations(items)` — observation state.
- `getReadiness()` — derived availability.
- `getEffectiveSources()` — derived provenance used by the UI.
- `subscribe(listener)` — observe state changes.
- `reset()` — reset only this frontend contract state.

## Migration strategy

This is deliberately a boundary layer, not a big-bang rewrite. Existing modules can continue emitting their current events. Subsequent work should migrate one owner at a time to this state contract, then remove redundant local state/bridges after tests confirm equivalence.
