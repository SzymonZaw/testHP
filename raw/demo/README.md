# Demo dataset

This directory contains a tiny, synthetic dataset for exercising the research pipeline without committing real or sensitive biological data.

It is intentionally small and deterministic. Values are illustrative and **not clinical measurements**.

The fixture contains:

- normal longitudinal variation;
- one low-quality observation;
- a longitudinal change in inflammation;
- a possible change point in bone density;
- modality disagreement at one timepoint;
- enough uncertainty to exercise `insufficient_evidence` / additional-measurement logic.

Files:

- `observations.csv` — synthetic multimodal observations;
- `metadata.json` — dataset provenance and expected test scenarios.
