# Hand Surface Digital Twin · Stages 0–8

This branch consolidates the hand-surface direction into one runtime contract. The existing progressive navigation remains the source of spatial truth; the hand-surface engine adds a visual context layer instead of replacing the evidence/navigation model.

## Runtime contract

- **Stage 0 — Viewport ownership:** `context` and `focus` are separate. A deep view owns input while the macro canvas becomes non-interactive. A hidden/0×0 base canvas is valid when explicitly isolated by the focus view.
- **Stage 1 — Real Hand Surface:** a procedural 3D hand mesh is rendered as a fallback surface. It supports orbit, zoom and region context without requiring a flat image plane.
- **Stage 2 — Coordinate System:** the engine exposes a hand-local coordinate system and named landmarks with confidence. These coordinates are the registration anchor for later observations.
- **Stage 3 — Real Skin Evidence:** registered hand observations are loaded from `/api/hand/analysis` and their image assets are treated as evidence, not as UI decoration.
- **Stage 4 — Multi-view projection:** available `front`, `back`, `side_left`, `side_right` and `thumb` observations are selected according to the current camera azimuth. The selected texture is applied to the 3D surface; the procedural texture remains the fallback.
- **Stage 5 — Evidence Layer:** the current spatial target is kept separate from the visual surface. Evidence is explicitly attached to a spatial target and is never inferred merely because a deeper node exists.
- **Stage 6 — Anatomy:** a lightweight skeleton layer is present behind the skin and can be revealed through controlled opacity when the user drills deeper.
- **Stage 7 — Progressive Resolution:** macro skin remains as context while tissue/cellular/cell navigation becomes the focus. Input ownership follows the focus view.
- **Stage 8 — Longitudinal Twin:** subject and timepoint are explicit in the engine state. The model is ready to bind T1/T2/T3 observations without changing spatial IDs.

## What is intentionally not claimed

The current projection is a **registration-ready prototype**, not clinical-grade photogrammetry. Multi-view blending, camera calibration, lens correction, dense surface registration and texture seam optimization still require real capture metadata and validation images.

Likewise, the skeleton is a spatial reference scaffold, not a validated anatomical reconstruction.

## Debug contract

`window.handSurfaceEngine.snapshot()` reports:

- viewport ownership and input owner,
- surface renderer and opacity state,
- landmark count and coordinate space,
- loaded skin evidence and selected view,
- projection strategy and quality score,
- explicit evidence target,
- progressive-resolution context/focus state,
- longitudinal subject/timepoint readiness.

This makes `canvas: 0×0`, hidden base rendering and deep-view ownership distinguishable from an actual renderer failure.
