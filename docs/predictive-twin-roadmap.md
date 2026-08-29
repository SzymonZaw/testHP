# Predictive Biological Twin — Research Roadmap

This document defines the implementation boundary for the next-generation research layer in `dev/next-cleanup`.

## 1. Mechanistic multiscale simulation

The research engine now exposes explicit state contracts across:

```text
molecular
   ↓
cell
   ↓
tissue
   ↓
organ
   ↓
organism
```

The simulator also accepts higher-level context and returns a trace showing how
local cell state propagates upward. This is a deterministic baseline only. It
is **not** a validated physiological model.

The intended scientific evolution is:

```text
DNA / epigenetics
       ↓
gene expression
       ↓
proteins
       ↓
metabolism
       ↓
cell state
       ↓
tissue state
       ↓
organ function
       ↓
whole-body state
```

with explicit feedback from tissue/organ/organism context back into lower-level
models.

## 2. Long-horizon prediction

Standard research horizons are:

```text
5 years → 20 years → 50 years → 100 years
```

Every prediction carries a model version, an uncertainty value and an explicit
`validated=False` flag. A 100-year scenario is therefore a model scenario, not
a claim about survival or health at age 100+.

The 200-year objective belongs to the long-term research program. It is not a
capability demonstrated by the current software.

## 3. Rejuvenation candidate localization

The planner ranks spatial/biological nodes using priority, confidence and
evidence. When evidence or confidence is insufficient it returns
`insufficient_evidence` rather than recommending an intervention.

A research candidate can be represented as:

```text
problem localization
        ↓
severity / priority
        ↓
confidence
        ↓
evidence sufficiency
        ↓
research candidate intervention class
```

The planner does not prescribe a therapy or execute a medical action.

## 4. Whole-body twin

`WholeBodyTwin` provides a hierarchical container that can represent:

```text
organism → organ → tissue → cell → molecular
```

This is the structural foundation for extending the current hand-focused twin
to a whole-body model. It does not yet provide a complete whole-body
physiological simulator.

## 5. Clinical and scientific validation gates

The validation plan is explicitly staged:

```text
unit / deterministic validation
        ↓
analytical validation
        ↓
benchmark datasets
        ↓
internal validation
        ↓
external validation
        ↓
longitudinal cohorts
        ↓
prospective validation
        ↓
clinical utility
        ↓
safety / regulatory review
```

The predictive modules must remain research-only until appropriate evidence
supports each claim. A software test passing is not evidence of clinical
validity.

## Current implementation status

Implemented in `research/predictive_twin.py`:

- molecular/cell/tissue/organ/organism state contracts;
- bottom-up state aggregation;
- top-down contextual simulation;
- 5/20/50/100-year research scenarios;
- explicit horizon uncertainty;
- research-only cell health assessment;
- calibrated-feature cell-age contract;
- evidence-gated rejuvenation candidate ranking;
- whole-body hierarchy and ancestor/descendant traversal;
- staged clinical-validation gates;
- 200-year longevity scenarios explicitly marked research-only.

The next scientific work is not to increase the number of scores. It is to
replace deterministic placeholders with experimentally grounded models,
validated biomarkers, calibrated uncertainty and reproducible longitudinal
data while preserving these contracts.
