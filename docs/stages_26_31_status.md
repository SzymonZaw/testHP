# Hand Surface — stages 26–31

## Stage 26 — evidence scope gate

Evidence is validated by `subject_id + timepoint + spatial_id`; `biological_level` remains a separate dimension. Direct evidence and recursive descendant evidence are reported separately. Sibling and ancestor evidence cannot silently enter the selected scope.

## Stage 27 — research manifest

A manifest joins the concrete twin package with its evidence-scope result and software version. The manifest has a deterministic fingerprint and retains the exact `spatial_id`.

## Stage 28 — run ledger

Each prospective projection run receives an auditable ledger entry containing identity, manifest fingerprint, worker status and execution state. A ready handoff is not execution.

## Stage 29 — portable research bundle

The package, evidence manifest, worker request, ledger and reproducibility record are assembled into one metadata-only bundle. The bundle is fingerprinted for later comparison.

## Stage 30 — acceptance gate

The final gate checks package QA, projection-plan QA and cross-module identity. `spatial_id`, subject and timepoint must agree across package, manifest, worker request and ledger.

## Stage 31 — research trace

A compact trace exposes accepted/blocked status, bundle fingerprint and the scientific boundary. It explicitly states that no anatomy reconstruction or diagnosis was performed.

## Runtime sequence

`observations/evidence scope → package → manifest → run ledger → worker handoff → research bundle → acceptance → trace`

## Scientific boundary

Stages 26–31 improve provenance, scope integrity and reproducibility. They do not manufacture biological evidence, infer missing anatomy, diagnose disease, or claim photogrammetrically accurate reconstruction.
