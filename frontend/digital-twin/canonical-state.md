# Canonical Digital Twin State

All Digital Twin UI modules should consume one canonical state. Do not create a second source of truth for evidence, QC, biological age, health, molecular state, provenance, validation or intervention priority.

```text
DigitalTwinState
├── input
├── modalities
├── qc
├── anatomy
│   ├── hand
│   ├── regions
│   ├── tissues
│   └── cells
├── molecular
│   ├── rna
│   ├── proteomics
│   ├── epigenetics
│   └── genomics
├── health
├── biologicalAge
├── evidence
├── uncertainty
├── provenance
├── validation
└── interventions
```

Backend `AnalysisResult` is normalized once at the boundary and reduced into this state. UI components should read from the canonical state and must not infer a biological result from missing data.

Status distinctions are preserved:

- QC: `missing`, `unusable`, `usable`
- biological inference: `not_established`, `available`
- health: `healthy`, `at_risk`, `diseased`, `unknown`

This state is a frontend integration contract, not a biological model.
