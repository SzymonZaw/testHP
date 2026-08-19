# Hand Surface · Stages 9–10 complete

## Stage 9 — real skin surface

The macro hand view now uses a curved procedural hand surface instead of a flat image plane. Registered hand assets are loaded from `/api/hand/analysis` and `/api/hand/evidence/{asset_id}`.

Supported view labels:

- `front`
- `back`
- `left`
- `right`

The renderer blends those views using the surface normal. This is a deterministic multi-view projection prototype; it does **not** claim subject-specific photogrammetry or validated landmark registration.

The original evidence files remain the source of truth. The 3D projection is a visualization layer and never creates biological evidence.

## Stage 10 — anatomical scaffold

A separate scaffold is rendered behind/through the skin surface. It contains a spatial reference for:

- bones
- joints
- thumb support
- finger segments

The scaffold has independent visibility and does not own pointer input. Its presence cannot create evidence or biological conclusions.

## Input ownership

At macro level:

```text
hand surface   = input owner
scaffold       = visual context only
base canvas    = fallback navigation target
```

At tissue/cellular/single-cell level:

```text
deep drill     = input owner
hand surface    = pointer-events:none
base canvas     = hidden/isolated by viewport controller
```

Only one layer owns interaction at a time.

## Evidence status

The UI reports which real photo views were loaded. Missing views fall back to the anatomical material rather than inventing imagery.

The projected appearance is therefore allowed to be partial. A missing photograph is never treated as evidence of the corresponding surface region.

## Next technical step

For a subject-specific high-fidelity twin, add an offline registration pipeline that stores camera calibration, landmarks, UV/surface correspondences and confidence per source image. The browser renderer should consume that registration artifact rather than infer it at runtime.
