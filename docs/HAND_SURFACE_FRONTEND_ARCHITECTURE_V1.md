# Hand surface frontend architecture v1

Branch: `dev/next-cleanup`

This document defines stages 1-5 of the frontend cleanup. It is deliberately a contract first: UI modules must consume these rules instead of inventing their own source or geometry ownership.

## 1. Two explicit hand modes

- `classic` — procedural/parametric hand geometry; sliders are authoritative.
- `real` — geometry/data backed by real user evidence and measurements.

Classic is always available. Real is available only when real evidence exists. Selecting real when no real evidence exists resolves back to classic with an explicit reason in `mode_resolution`.

The two modes are not silently blended. Real measurements/photos do not overwrite classic slider state, and classic geometry is not presented as measured anatomy.

## 2. Canonical input sources

Supported source kinds:

- `default`
- `classic-geometry`
- `measurement`
- `photo`
- `prepared-photo`
- `registered-photo`
- `reconstruction`
- `observation`
- `microscopy`
- `molecular`

Every source carries provenance, status, asset/evidence id when available, and a spatial id when available.

Layer mapping:

| Layer | Typical inputs |
|---|---|
| macro | hand photos, measurements, observations, reconstruction |
| tissue | WSI / microscopy, linked observations |
| cellular | microscopy / cellular evidence, linked molecular data |
| cell | explicit cell-level evidence; otherwise navigation only |

A source is never inherited merely because a user navigated deeper. Evidence must be explicitly linked to a target to be treated as evidence for that target.

## 3. Layer contract

Each layer uses `hand-layer-contract-v1` with:

- `layer`
- `spatial_id`
- `geometry`
- `measurements[]`
- `images[]`
- `observations[]`
- `microscopy[]`
- `molecular[]`
- `all_sources[]`
- an explicit research/interpretation boundary

The frontend may render empty states, but it must not manufacture evidence or silently change source ownership.

## 4. 3D projection ownership

Photo projection belongs to the canonical Three.js **scene**, not to the currently selected macro/deep geometry root.

Invariant:

> Changing spatial depth must not move, rescale, recreate, or re-parent an already applied photo projection into `deepRoot`.

`deep-viewport-sync.js` now marks the scene with `hand-surface-projection-anchor-v1` metadata and repairs accidental projection parenting back to the canonical scene.

The existing photo projection group is named `__photo_surface_projection__`. The cleanup does not create a second renderer or a second Three.js scene.

## 5. Deterministic mode resolution

Mode resolution is centralized in `hand-surface-architecture-v1.js`.

Resolution rules:

1. Classic is always valid.
2. Real requires at least one real-data source.
3. An explicit real selection is respected only when real data is available.
4. If real data disappears, effective mode becomes classic; the reason is retained.
5. UI modules should use the effective mode rather than independently deciding which controls to display.

The canonical state is stored under `digitalTwinHandSurfaceArchitecture.v1` and exposes:

- `testhpHandSurfaceArchitecture`
- `testhp:hand-surface-mode-changed`
- `testhp:hand-surface-layer-contract-changed`
- `testhp:hand-surface-architecture-synced`

## Integration

The already-loaded `deep-viewport-sync.js` loads the architecture and mode bridge once. Both loaders are singleton-safe and do not start polling loops or duplicate renderers.

The existing `hand-geometry-mode-switch.js` remains the visible mode UI. The new bridge synchronizes its `classic` / `real` choice with the canonical architecture state.
