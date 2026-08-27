# Phase G-I — Time, Digital Twin and clinical governance

## Phase G — Time

### 26. Longitudinal comparison

`LongitudinalObservation` binds measurements to subject, hand and timepoint. Comparisons should use explicit feature spaces and source IDs rather than comparing arbitrary UI values.

### 27. Biological age

`BiologicalAgeEstimate` is a model output, not a fact. It records model/version, source observations, uncertainty and validation status. A single age number must never replace the underlying evidence.

### 28. Aging trajectory

`Trajectory(kind="aging")` requires multiple timepoints. The trajectory retains the observations used to derive it and may identify the model producing the trend.

### 29. Disease trajectory

`Trajectory(kind="disease")` uses the same longitudinal lineage. Disease progression must be represented as an evidence-backed trajectory, not a diagnosis inferred from a single snapshot.

## Phase H — Digital Twin

### 30. Unified spatial model

`SpatialModel` defines one hand reference frame and records the objects, scales and registration IDs included in the model.

### 31. Cross-scale navigation

`CrossScaleLink` maps parent/child objects across scales and requires evidence. A visual zoom is not itself a biological mapping.

### 32. State estimation

`StateEstimate` stores a model-generated state vector with source observations, model identity/version and uncertainty.

### 33. Uncertainty

Uncertainty is retained at inference boundaries instead of being discarded when data are combined. Missing evidence should remain missing/unknown.

### 34. What-if simulation

`WhatIfScenario` separates assumptions and proposed interventions from observed state. Simulation output must be marked as simulated and retain uncertainty; it is not a treatment recommendation.

## Phase I — Clinical

### 35. Risk assessment

`RiskAssessment` records target, horizon, score, evidence, uncertainty and model validation status. Risk is not diagnosis.

### 36. Intervention support

`InterventionSupport` represents evidence-backed candidate options. Clinical review remains explicitly required by default.

### 37. Validation

`ValidationRecord` records dataset/cohort, metrics, protocol and validation status. Model versions are immutable identifiers for downstream auditability.

### 38. Clinical/regulatory layer

`ClinicalRegulatoryRecord` defines intended use, contraindications, human oversight, audit trail, data governance and regulatory status.

## Critical architecture rule

```text
observations
    ↓
validated inference
    ↓
state / trajectory
    ↓
digital twin
    ↓
risk / simulation
    ↓
clinical review
```

The system must never silently turn a research estimate into a clinical decision. Research, validated clinical models and regulatory status are explicit states.

## Long-term goal

The architecture can eventually support longitudinal biological-age research and individualized hand-state modelling, but this phase does not claim that any current model can reliably determine lifespan, cellular age, disease, rejuvenation need or treatment response.
