# Biological models

Reserved backend boundary for evidence-backed biological inference. Modules in this package must not invent biological results. Until a model is registered and validated for the requested tissue/cell population and modality, the result must remain `not_established`.

## Planned domains

- `contracts/` — stable output contracts for age, health, molecular state, multimodal state and intervention priority.
- `registry/` — model metadata and validation metadata.
- `age/` — cell, tissue, region and hand biological-age estimators.
- `health/` — cell, tissue, region and hand health-state estimators.
- `molecular/` — RNA, proteomics and epigenetics state/feature adapters.
- `multimodal/` — evidence fusion, state integration and uncertainty propagation.
- `intervention/` — evidence-based priority only; no clinical treatment recommendations without appropriate validation.

## Status semantics

`not_established` means that the system does not currently have an appropriately validated model for the requested inference. Missing data must never be silently converted to `healthy` or to a numerical biological age.
