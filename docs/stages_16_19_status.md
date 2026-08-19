# Hand Surface — stages 16–19

## Stage 16 — foreground / background quality

Introduces an explicit `SegmentationMask` contract. A prepared photograph is not silently accepted as a hand surface: foreground ratio, resolution, confidence and edge quality are recorded. Low-confidence segmentation remains reviewable instead of becoming fabricated geometry.

## Stage 17 — camera registration

Introduces `CameraView` and a common `hand-surface-v1` coordinate system. Camera position, target, focal length and distortion are metadata. A view is considered registered only when it uses a supported view and finite coordinates.

## Stage 18 — natural geometry calibration

Introduces explicit calibration parameters for scale, palm width/length, finger spread, thumb angle, thickness and smoothness. Geometry changes can be measured with `deformation_distance`, making manual tuning inspectable rather than implicit.

## Stage 19 — multi-view projection runtime

Adds weighted candidate selection for surface points. The runtime prefers camera alignment and image quality while accounting for distance. It records which observation supplied a surface point and preserves provenance.

### Safety / evidence boundary

These stages prepare the application for a real projection worker. They do **not** perform photogrammetry, invent missing anatomy, diagnose pathology, or claim that a photograph is a validated 3D reconstruction. A production reconstruction step should be added only after real test photographs and calibration data are available.

### Runtime sequence

`raw/prepared image → segmentation QA → camera registration → geometry calibration → weighted surface projection → provenance`
