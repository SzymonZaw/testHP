# Hand Surface — stages 16–20

## Stage 16 — foreground / background quality

`SegmentationMask` records foreground ratio, resolution, confidence and edge-quality metadata. Low-confidence segmentation remains reviewable; it is never silently converted into anatomy.

## Stage 17 — camera registration

`CameraView` records a supported view, camera position/target, focal length and distortion in the shared `hand-surface-v1` coordinate system. Registration validity requires finite coordinates and a supported view.

## Stage 18 — natural geometry calibration

`GeometryCalibration` makes scale, palm dimensions, finger spread, thumb angle, thickness and smoothness explicit. `deformation_distance` exposes geometry changes as a deterministic QA metric.

## Stage 19 — multi-view projection runtime

`ProjectionCandidate` and `select_projection_source` choose a weighted source using camera alignment, distance and image quality while preserving the selected asset/view as provenance. This is a projection contract, not photogrammetry.

## Stage 20 — registration QA

`registration_quality_report` checks structural coverage of the five supported surface views. It reports ready and incomplete views, usable segmentation count, valid camera count and coverage. It explicitly exposes `accuracy_claim: false` so QA readiness cannot be mistaken for anatomical or photogrammetric accuracy.

The browser already exposes Stage 20 through the Hand Surface registration QA panel. The backend now exposes the same concept as a reusable manifest contract.

## Safety / evidence boundary

Stages 16–20 prepare the application for a real projection worker. They do not perform photogrammetry, invent missing anatomy, diagnose pathology, or claim that a photograph is a validated 3D reconstruction.

Runtime sequence:

`raw/prepared image → segmentation QA → camera registration → geometry calibration → weighted surface projection → registration QA → provenance`
