# Hand Surface — Stages 3–5

## Stage 3 — Multi-view evidence
- Load all ready/available hand photographs for the current subject/timepoint.
- Recognize front/back/left/right/thumb views.
- Keep each source asset and its view metadata visible to the renderer.
- Use deterministic view selection rather than picking the first asset.
- Blend overlapping projections by surface-facing confidence.

## Stage 4 — Registration and surface coordinates
- Introduce explicit surface-registration metadata.
- Store normalized landmarks and image-to-surface transforms separately from source images.
- Support a calibrated fallback when no manual registration exists.
- Expose registration quality and source view in debug output.
- Do not claim biological localization from an unregistered photograph.

## Stage 5 — Anatomical scaffold and observation overlays
- Add a separate anatomical scaffold layer below the skin surface.
- Keep bones/joints as spatial reference geometry, not as biological evidence.
- Add skin opacity control and scaffold visibility control.
- Preserve viewport ownership: macro surface owns macro input; deep views isolate their own input.
- Keep evidence overlays attached to spatial IDs and never infer evidence merely because a 3D region exists.

## Acceptance criteria
1. PHOTO/MODEL remains available at macro level.
2. Multiple source images can coexist without replacing the source metadata.
3. Registration status is explicit: registered, calibrated fallback, or unavailable.
4. Skeleton visibility never changes the evidence state.
5. Deep navigation remains input-isolated from the macro renderer.
6. Debug state identifies active view, viewport owner, visible layers, source assets, registration mode, and scaffold state.
