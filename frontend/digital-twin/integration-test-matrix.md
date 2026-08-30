# Digital Twin frontend integration test matrix

## 8 — Upload wizard

- choose each supported modality
- reject unsupported modality
- files move modality → upload → validation → analysis → digital_twin
- validation failure stays on validation
- analysis result enters canonical state

## 9 — Biological models

- established model displays its value and validation metadata
- `not_established` never displays a fabricated biological value
- missing/unusable input is distinct from model-not-established

## 10 — Full Digital Twin

- one `AnalysisResult` populates the canonical state
- anatomy, molecular, health, age, evidence, uncertainty and intervention read from that state
- 3D viewer continues to use the existing semantic viewer state

## 11 — Empty/error states

- no input → missing
- QC failure → unusable
- valid input without validated model → not_established
- validated result → validated
- absent health state → unknown

## 12 — Cleanup

- no legacy module is deleted while still referenced by bootstrap/imports
- canonical owner is documented before removal

## 13 — End-to-end

Minimum fixtures:

1. no data
2. image only
3. image + WSI
4. molecular-only
5. mixed modalities
6. unusable modality
7. unestablished model
8. validated model fixture

The biological model itself is not tested as clinically correct by this frontend suite; scientific/clinical validation belongs to the backend model and validation datasets.
