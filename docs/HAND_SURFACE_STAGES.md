# Hand surface roadmap — stages 0–2

## Stage 0 — surface architecture

**Goal:** make the macro hand a spatial surface that can host real observations without changing the progressive macro → tissue → cellular → cell model.

Implemented in this branch:

- a dedicated `hand-surface-canvas` owned only by the macro Hand view;
- explicit PHOTO / MODEL / RESET controls;
- macro photo loading through the existing hand evidence API;
- the original macro renderer remains the navigation/evidence authority;
- the surface renderer is visual context, not biological evidence;
- deep layers continue to replace the surface view when a deeper spatial target becomes active.

## Stage 1 — anatomical 3D hand surface

**Goal:** replace the capsule-like macro placeholder with a more hand-shaped continuous visual surface.

Implemented prototype:

- rounded palm volume;
- wrist transition;
- four fingers with different proportions and small angular differences;
- thumb with separate orientation and thenar-side joint volume;
- subtle crease geometry;
- physically lit skin material;
- orbit/zoom/reset interaction;
- no flat image plane is used for the hand itself.

This is deliberately a procedural research prototype, not a clinically accurate anatomical mesh.

## Stage 2 — real macro photograph projected onto the surface

**Goal:** use an actual registered hand photograph as an observation on the 3D surface rather than as a floating 2D image.

Implemented prototype:

- selects an available T0 hand `front` or `back` asset from `/api/hand/analysis`;
- loads the image through `/api/hand/evidence/{asset_id}`;
- projects the photograph in the hand material using world-position coordinates;
- blends the photo only on surfaces facing the projected view, leaving the 3D volume and lighting visible;
- PHOTO/MODEL switching makes the distinction between observation and anatomical surface explicit.

### Important limitation

Stage 2 is **projection infrastructure**, not final multi-view registration. The current projection assumes the selected photograph is approximately aligned to the prototype hand coordinate system. It does not yet solve landmark-based registration, camera calibration, occlusion masks, seam blending, color calibration or a texture atlas.

## Next stage

Stage 3 should add a proper registration record:

```text
original image
  → landmarks
  → camera / pose transform
  → surface correspondence
  → confidence / mask
  → projected texture
```

Only after that should `front`, `back`, `side_left`, `side_right` and `thumb` be fused into a multi-view surface atlas. The original observations must remain immutable and separately accessible.
