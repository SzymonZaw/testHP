# Hand Surface — stages 11–16

The Hand Surface workflow is target-scoped and remains separate from biological interpretation.

## Stage 11 — target-scoped surface manifest

Prepared images, registrations and runtime state use one canonical `spatial_id` for the active spatial target.

## Stage 12 — preparation readiness

Prepared photographs are counted by unique supported view. A duplicate view does not increase readiness.

## Stage 13 — registration readiness

A registration is valid only when the view is supported, prepared, and scoped to the same canonical target.

## Stage 14 — reconstruction readiness

A reconstruction cannot be marked ready until at least two prepared and registered views exist. Registered views must be a subset of prepared views.

## Stage 15 — surface asset

A reconstructed surface is represented explicitly by `SurfaceAsset`, with a reconstruction ID, source views, coordinate system and provenance. A ready asset is not the same thing as an applied asset.

## Stage 16 — surface application and segmentation boundary

`SurfaceApplication` records whether a ready surface was actually applied to the spatial model. Target and coordinate-system mismatches block application. Segmentation remains an explicit quality gate; low-confidence foreground separation does not silently become geometry.

## End-to-end state

`uploaded → prepared → registered → reconstruction-ready → surface-ready → applied-to-spatial-model`

Every state remains scoped to the same canonical spatial target.

## Evidence boundary

These contracts describe application state and reconstruction readiness. They do not claim clinical photogrammetry, anatomical inference, diagnosis, or a validated 3D reconstruction algorithm. A real reconstruction worker can consume the manifest once calibrated capture data and production reconstruction are available.
