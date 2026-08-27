# Surface T0 — acquisition and validation

The first trustworthy surface twin requires five gates:

1. **Camera calibration** — intrinsics and distortion come from measured calibration observations. Defaults are not considered calibrated.
2. **Metric scale** — every metric reconstruction needs a known physical reference or another independently validated scale source.
3. **Photo quality** — resolution, sharpness, exposure and hand-detection confidence are checked before reconstruction.
4. **Multi-view registration** — views are registered to a common camera/hand frame; failed correspondence is a blocking state.
5. **Reconstruction validation** — sparse/dense geometry must retain source views, method, quality and uncertainty. Reprojection is required before accepting the result as a Surface T0.

## Acceptance rule

```text
PASS = calibrated + metric scale + quality pass + registration pass + reconstruction validation
```

A failed gate must not be silently replaced with a default value. The resulting state remains explicit (`needs-calibration`, `insufficient-correspondence`, etc.).

## Metric scale

The current scale adapter records a known reference distance and derives `mm_per_pixel`. For multi-view metric reconstruction, the physical scale must ultimately be tied to the reconstructed coordinate frame, not merely copied from a 2D image.

## Quality

Thresholds in the reference implementation are conservative engineering gates, not clinical acceptance criteria. They must be tuned and validated against the actual camera/acquisition protocol.

## Current reconstruction scope

The current reconstruction implementation produces a sparse point cloud from calibrated consecutive views. It does **not** claim a dense, watertight anatomical mesh. Dense reconstruction and independent measurement validation are later milestones.
