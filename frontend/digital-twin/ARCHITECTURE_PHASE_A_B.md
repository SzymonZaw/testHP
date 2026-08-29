# Digital Twin architecture — Phase A/B foundation

Target branch: `dev/next-cleanup`

## Canonical hierarchy

`hand -> structure -> tissue -> cellular -> cell -> subcellular -> molecular`

The hierarchy is owned by `spatial-hierarchy.js`. Every evidence record and assessment must resolve to a canonical `spatialId`.

## Canonical twin

`digital-twin-core.js` owns the browser-side `DigitalTwin` envelope:

- `subjectId`
- `timepoint`
- `hand`
- `spatial`
- `evidence[]`
- `assessments[]`
- `timeline[]`

Feature modules should read from this envelope instead of creating parallel subject/region state.

## Data contract

`digital-twin-data-contract-v2.js` defines the canonical target, evidence and assessment shapes. The existing `hand-data-contract.js` remains available for backward compatibility during cleanup; it is not silently replaced.

Source semantics:

- `real` — directly observed/acquired
- `computed` — derived from real data
- `simulated` — synthetic/modelled
- `default` — UI/application fallback
- `missing` — no evidence

A visualization must never promote `simulated` or `default` into real biological evidence.

## Phase B foundation

`anatomy-tissue-model-v1.js` defines the frontend representation for anatomical structures and tissues. It intentionally does not fabricate anatomy or microscopy data. Real geometry and tissue evidence are attached by asset/evidence IDs.

`evidence-pipeline-v2.js` centralizes evidence registration, target lookup, availability summaries and source/status prioritization.

## UI stability rules

1. `main` is out of scope; work is restricted to `dev/next-cleanup`.
2. Existing UI modules remain compatible while the canonical foundation is introduced.
3. Spatial IDs are generated at the navigation layer, not normalized after rendering.
4. Deep views are navigation/visualization unless explicit evidence is linked to their target.
5. No clinical diagnosis is inferred from a visualization placeholder.

## Current boundary

This change establishes the canonical browser-side architecture and Phase B contracts. It does **not** claim that the project already has patient-specific 3D reconstruction, real tissue segmentation, single-cell microscopy, or validated clinical inference. Those require real acquisition/registration/model pipelines in later work.
