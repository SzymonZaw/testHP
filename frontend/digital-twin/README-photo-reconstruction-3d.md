# Photo 3D Reconstruction — stages 6–10

The module now has a single build flow: validate registered views → build visual-hull mesh → generate a portable texture asset when Pillow is available → persist reconstruction manifest → expose result/clear operations.

The current geometry method is `silhouette-envelope-v1`. It is intentionally conservative until calibrated camera intrinsics/extrinsics are available. It must not be presented as a calibrated multi-camera photogrammetry result.

Use `PhotoReconstruction3D.mount(container, subjectId, timepoint)` from `photo-reconstruction-3d.js` for the result panel.
