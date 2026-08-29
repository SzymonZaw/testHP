# Pathology, Temporal Twin, Personal Baseline and Risk Map

Scope: stages 5–8 of the biological pipeline. These are research/data-system specifications, not clinical diagnostic or treatment recommendations.

## 5. Real pathology

Pathology analysis should be downstream of a well-characterized healthy reference and must distinguish normal biological variation from disease-related signals.

```text
Normal variation
       ↓
Alteration
       ↓
Pathological signal
       ↓
Localization
       ↓
Expert validation
```

### Requirements

1. Define healthy/reference distributions separately by tissue, cell type, modality and relevant context.
2. Represent normal biological variation explicitly.
3. Detect candidate anomalies without automatically calling them pathology.
4. Classify candidate changes only where reference data support the label.
5. Localize signals to cell, cluster, tissue and 3D region.
6. Preserve alternative hypotheses and `Unknown` outcomes.
7. Attach evidence, model/version, dataset provenance and uncertainty.
8. Validate against independent data and expert annotations.

Output is a localized research finding, not an autonomous diagnosis.

## 6. Temporal Twin

Goal: represent longitudinal change using repeated measurements from the same subjects.

```text
T0 → T1 → T2 → T3 → ...
```

### Requirements

- Stable subject/hand/tissue/timepoint identifiers.
- Acquisition metadata and provenance for every timepoint.
- Spatial registration/alignment across measurements.
- Tracking of structures across time.
- Cell tracking only where imaging and biological evidence make identity sufficiently defensible.
- T0/T1/T2 comparison with explicit measurement uncertainty.
- Change magnitude, direction and rate where statistically supported.
- Detection of unusual acceleration only relative to an appropriate baseline/reference.
- Complete longitudinal history.

The system must not infer a trend from cross-sectional observations as though they were longitudinal measurements.

## 7. Personal Baseline

Goal: characterize an individual's normal state from their own longitudinal history.

```text
My normal
    ↓
Current state
    ↓
Deviation
    ↓
Trend
```

### Requirements

1. Build baseline only from attributable observations with known quality.
2. Estimate normal ranges/distributions for the individual.
3. Account for individual variability and measurement noise.
4. Compare current state with the personal baseline first.
5. Use population reference as a secondary context, not a replacement for personal history.
6. Update the baseline as new longitudinal data arrive.
7. Preserve baseline versions so historical conclusions remain reproducible.
8. Distinguish true change from changes caused by acquisition, preprocessing or registration.

A deviation from personal baseline is a signal for further evaluation, not by itself a diagnosis.

## 8. Risk Map

Goal: aggregate validated biological signals spatially while retaining their evidence and uncertainty.

```text
Cell
 ↓
Tissue
 ↓
Region
 ↓
Hand
 ↓
Risk
```

### Requirements

1. Aggregate cell-level evidence using explicit, versioned rules/models.
2. Propagate uncertainty rather than hiding it during aggregation.
3. Aggregate to tissue and anatomical-region levels.
4. Preserve the spatial provenance of every risk contribution.
5. Define and validate risk categories against appropriate reference outcomes.
6. Attach confidence and evidence at every aggregation level.
7. Visualize risk in 3D without implying greater certainty than the underlying data support.
8. Keep `Unknown`/insufficient-evidence states visible.

Illustrative display categories may be:

```text
🟢 normal
🟡 monitor
🟠 elevated
🔴 high
```

These labels are presentation categories only until a validated risk model establishes their meaning. Risk output is decision support and must not be presented as an automatic medical decision.

## Cross-stage invariant

```text
Observation
   ↓
Evidence
   ↓
Inference
   ↓
Uncertainty
   ↓
Validation
   ↓
Spatial / temporal aggregation
```

Every downstream result must remain traceable to the underlying observations, model and validation context.
