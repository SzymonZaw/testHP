# Phase B — MRI/US to hand spatial registration

## Boundary

Imaging data and its native geometry are not assumed to be in hand coordinates. A registration result must explicitly map a source frame into the canonical `HandCoordinateSystem`.

```text
MRI / US native frame
        |
        v
  registration method
        |
        v
transform + quality + uncertainty
        |
        v
HAND_REFERENCE_FRAME
```

## Supported registration methods

- landmark
- rigid
- affine
- deformable
- manual
- external

The code records the method and provenance but does not claim that a method is clinically validated for a particular modality or anatomy.

## Required evidence

A registration requires source data IDs, source image geometry, a target hand frame, an explicit transform, quality and uncertainty fields. Landmark registration additionally requires landmarks.

## Production integration

A validated imaging-registration backend (for example an ITK/ANTs/3D Slicer-based pipeline appropriate to the study protocol) should produce the transform and metrics. The application consumes that result; it must not silently manufacture one.

## Acceptance criteria

1. Native image frame is preserved.
2. Target is a specific subject/hand/timepoint hand frame.
3. Transform is explicit.
4. Quality and uncertainty are retained.
5. Registration provenance is retained.
6. Failed/untrusted registration can remain outside the registered state.
7. Anatomical segmentation can consume only explicitly registered source geometry.
