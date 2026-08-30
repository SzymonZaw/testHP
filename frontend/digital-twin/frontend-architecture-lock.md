# Frontend architecture lock — Digital Twin

## Canonical flow

```text
Backend
  ↓
AnalysisResult
  ↓
normalize / adapter
  ↓
DigitalTwinState
  ↓
canonical UI projections
  ↓
all UI
```

`DigitalTwinState` is the only source of truth for analysis-derived UI data.

## Ownership

- Evidence: `state.evidence`, `state.qc`, `state.provenance`, `state.validation`, `state.uncertainty`
- Health: `state.health` + canonical anatomy hierarchy
- Biological age: `state.biologicalAge`
- Molecular: `state.molecular`
- Cells: `state.anatomy.cells`
- Intervention: `state.interventions`
- 3D semantic state: projection of canonical anatomy/health/evidence

UI components must not maintain alternate analysis values for these domains.

## API rule

Only the canonical runtime may retrieve an `AnalysisResult`. Components must not independently `fetch()` analysis data, parse backend contracts, or infer biological conclusions.

## State semantics

Loading, error, missing data, unusable data, unestablished models and validated results are distinct states. Missing or unvalidated data must never become a synthetic biological age, healthy label, or intervention recommendation.

## Fixtures

Fixtures live under `frontend/digital-twin/fixtures/` and are restricted to tests/local development. They are never production fallbacks.

## Legacy migration

Existing feature modules may remain during migration. A module is removable only after its analysis-derived state has been migrated to the canonical state and its integration path is covered by tests.
