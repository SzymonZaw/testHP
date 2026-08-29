# Cell Health and Biological Age

Scope: stages 3–4 of the real biological pipeline. These specifications define data and validation requirements; they do not constitute a clinical diagnostic model.

## 3. Real Cell Health

Goal: represent biological cell state from measurable evidence without assuming that morphology alone is sufficient.

### State ontology

```text
Healthy
Altered
Stressed
Senescent
Damaged
Pathological
Unknown
```

The ontology must be versioned. Labels are not interchangeable: for example, stress, damage and senescence require distinct biological evidence and may coexist as observations even when a single display category is selected.

### Required work

1. Define operational biological criteria for every state.
2. Define exclusion criteria and ambiguous/unknown cases.
3. Build reference datasets with provenance and tissue/cell-type context.
4. Link each label to measurable evidence and, where possible, expert annotations.
5. Define feature groups: morphology, spatial context, markers and molecular measurements.
6. Establish subject/sample-level train/validation/test separation.
7. Train candidate health-state models only after labels and evidence rules are fixed.
8. Produce state probabilities/confidence rather than unsupported binary claims.
9. Preserve evidence, model version, dataset version and uncertainty with every inference.
10. Validate against independent data and expert review.

### Output contract

```text
Cell
 ↓
Health state distribution
 ↓
confidence / uncertainty
 ↓
evidence
 ↓
model + dataset provenance
```

If evidence is insufficient or outside the validated domain, the result must be `Unknown` rather than a forced health classification.

## 4. Real Biological Age

Goal: estimate an age-related biological state appropriate to cell type and context, with calibrated uncertainty.

### Pipeline

```text
Reference population
        ↓
Aging biomarkers
        ↓
Cell-type-specific model
        ↓
Calibration
        ↓
Independent validation
        ↓
Age estimate + uncertainty
```

### Required work

1. Define what “biological age” means for each supported cell type/context.
2. Assemble reference populations spanning relevant chronological ages and biological variation.
3. Select and validate aging biomarkers; record measurement method and provenance.
4. Build cell-type-specific models where justified by data.
5. Prevent subject/sample leakage between training and evaluation.
6. Calibrate predicted distributions and assess calibration on held-out data.
7. Report prediction intervals/confidence intervals and uncertainty sources.
8. Test robustness across batches, sites, modalities and demographic/contextual strata where applicable.
9. Validate on an independent dataset not used during model development.
10. Preserve model, dataset, biomarker and calibration versions in evidence/provenance.

### Output contract

```text
Chronological age: 65

Estimated biological state:
68–74

Uncertainty:
...

Evidence:
...
```

The system must not reduce this to an unsupported scalar such as `Cell age = 71`. A biological-age estimate is model output with uncertainty and context, not a directly observed property of an individual cell.

## Validation gates

Neither Cell Health nor Biological Age should be presented as clinically established until the relevant biological definitions, datasets, model performance, calibration and independent validation have been completed. Unknown and out-of-distribution cases remain first-class outcomes.
