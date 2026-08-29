# Research status and anti-overclaim policy

This repository separates **implemented software**, **research scaffolds**, and **validated scientific capabilities**.

## Implemented now

- spatial hand / multiscale data contracts
- evidence and provenance plumbing
- cell/tissue analysis primitives
- longitudinal analysis primitives
- deterministic research-stage multiscale simulation
- prediction interfaces with explicit uncertainty
- candidate-region ranking for further investigation
- organism/organ/tissue/cell hierarchy
- benchmark and validation contracts

## Not established by code alone

The repository does **not** currently establish that it can:

- diagnose a disease from a single cell;
- determine a cell's true biological age;
- predict an individual's state 20–100+ years into the future with validated accuracy;
- determine that a rejuvenation intervention will work or is safe;
- simulate human biology mechanistically at sufficient fidelity for clinical use;
- predict survival to 200 years;
- provide clinical decisions.

These remain research hypotheses until supported by appropriate data and validation.

## Required scientific progression

```text
real observations
  -> reproducible preprocessing
  -> labeled benchmark
  -> simple baseline
  -> multiscale model
  -> held-out validation
  -> external validation
  -> longitudinal calibration
  -> prospective validation
  -> clinical utility / safety evidence
```

A module existing in Python is never counted as a validated biological capability.

## First falsifiable vertical slice

The primary near-term question is:

> Does adding multiscale evidence from cells/tissues improve prediction of a future hand-function measurement compared with a simple baseline, on held-out subjects?

Success requires reporting MAE/RMSE, uncertainty calibration, sample counts, missingness, subgroup performance, and comparison with the baseline. The result must be reproducible and externally testable.

## Long-horizon predictions

5/20/50/100+ year outputs are research scenarios. Uncertainty must be reported and evaluated against future observations whenever such observations become available. Longer horizon does not mean higher confidence.

## Rejuvenation

The system may rank regions for further investigation. It must not convert a score into a treatment recommendation without a separate evidence and safety layer.

## 200-year objective

The 200-year objective is a long-term research hypothesis. It is not a model output, guarantee, or current product capability.
