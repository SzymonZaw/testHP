# Hand Surface — stages 21–25

## Stage 21 — projection-plan QA

The browser already creates a deterministic `surface-projection-v2` source-selection plan. The backend now validates the same semantics: target, supported views, quality/weight ranges, minimum prepared views and confidence threshold. Validation never performs projection and never converts a low-confidence plan into a reconstruction.

## Stage 22 — portable twin package

A `TwinPackage` records `subject_id`, `timepoint`, `spatial_id`, coordinate system, geometry, mappings, projection plan, evidence identifiers and provenance. Evidence IDs remain explicit; the package does not infer evidence from filenames or spatial labels.

## Stage 23 — package integrity / evidence boundary

Package validation checks identity, spatial target, coordinate-system consistency, projection-plan presence and evidence references. A package with no evidence is not silently treated as biologically complete.

The spatial identity remains independent from `biological_level`: a package targets a concrete `spatial_id`, while biological layer is a separate dimension.

## Stage 24 — projection-worker handoff

`build_projection_worker_request()` creates an explicit request for a future projection worker. It is either `ready-for-worker` or `blocked` by QA. The request records the exact spatial target, evidence IDs and projection plan. `execution.performed` is always false in this contract; no browser-side claim of real photogrammetry is made.

## Stage 25 — reproducibility record

Every exported research run can be represented by a deterministic SHA-256 fingerprint over its canonical request payload plus software version and generation timestamp. This supports audit/reproduction of the *run definition*, not a claim that pixels or anatomy have been reconstructed accurately.

## Runtime sequence

`prepared evidence → registration QA → projection plan → package validation → worker handoff → reproducibility fingerprint`

## Scientific boundary

Stages 21–25 do not diagnose disease, infer missing anatomy, manufacture biological evidence, or claim clinically/photogrammetrically accurate 3D reconstruction. Missing or insufficient inputs remain explicit.
