# Validation and benchmark plan — Stages 14–15

## Validation levels

### V0 — input validity

- file exists
- format readable
- required metadata present
- no unexpected corruption

### V1 — measurement correctness

Check deterministic measurements against known inputs and reference implementations.

### V2 — algorithmic validation

Evaluate segmentation, landmarking, feature extraction, QC and other modality-specific algorithms against appropriate labelled/reference data.

### V3 — biological validation

For biological interpretations require appropriate reference cohorts, labels/assays and a predefined evaluation protocol.

### V4 — external validation

Test on data not used to develop the method, including different acquisition settings and datasets.

### V5 — prospective/clinical validation

Only after analytical validity and external validation are established should prospective or clinical evaluation be considered.

## Required reporting

Each validated analysis should report, where applicable:

- sensitivity,
- specificity,
- precision/recall,
- calibration,
- uncertainty,
- reproducibility,
- robustness to acquisition variation,
- missing-data behaviour,
- failure modes,
- subgroup performance,
- external-dataset performance.

Not every metric applies to every task. The metric set must be defined before evaluation.

## Reproducibility

A result should be reproducible from:

`run ID + source version + analysis version + parameters + input identifiers`

## Stage 15 boundary

The project is a research platform. Benchmark success does not itself establish clinical utility, diagnosis capability or regulatory readiness.
