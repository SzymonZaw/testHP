# Reference Population, Intervention Layer and Frontend Architecture

> Target architecture for `dev/next-cleanup`. This document defines missing structural layers; it does not imply that the scientific models are already validated.

## 16. 🟠 Reference population

Reference data is required before the system can meaningfully describe observations as normal, atypical, age-associated, or otherwise abnormal.

```text
reference/
├── populations/
├── cohorts/
├── demographics/
├── age_distributions/
├── normal_ranges/
├── biomarkers/
├── tissue_effects/
├── region_effects/
├── sex_effects/
├── batch_effects/
└── provenance/
```

Conceptually:

```text
Population
 ↓
Cohort
 ↓
Reference observations
 ↓
Normal ranges
 ↓
Age distribution
 ↓
Sex / tissue / region effects
 ↓
Reference biomarkers
 ↓
Reference model
```

A reference record should retain:

```text
ReferenceRecord
 ├── reference_id
 ├── population_id
 ├── cohort_id
 ├── age_range
 ├── demographic_context
 ├── tissue
 ├── anatomical_region
 ├── biomarker
 ├── value_distribution
 ├── normal_range
 ├── methodology
 ├── sample_count
 ├── quality
 ├── provenance
 └── version
```

### Required backend responsibilities

- cohort and population registry;
- reference biomarker registry;
- age-stratified distributions;
- tissue- and region-specific baselines;
- demographic stratification;
- reference-data quality control;
- provenance and versioning;
- comparison APIs;
- explicit applicability checks.

The backend should never silently classify an observation as abnormal merely because it differs from an arbitrary global threshold.

---

## 17. 🟠 Intervention layer

The intervention layer is a future decision-support boundary. It should be architected separately from observation, analysis, and diagnosis.

```text
intervention/
├── candidates/
├── indications/
├── contraindications/
├── expected_benefit/
├── risk_models/
├── response_models/
├── outcome_tracking/
├── intervention_history/
└── evidence/
```

Conceptually:

```text
Disease / risk signal
        ↓
Evidence assessment
        ↓
Possible intervention
        ↓
Expected benefit
        ↓
Risk / contraindications
        ↓
Expected response
        ↓
Outcome observation
        ↓
Updated twin
```

The layer must distinguish:

```text
observation
    ≠
prediction
    ≠
risk estimate
    ≠
intervention candidate
    ≠
clinical recommendation
```

For future use, an intervention record should contain:

```text
InterventionAssessment
 ├── assessment_id
 ├── subject_id
 ├── target_region
 ├── target_condition
 ├── evidence
 ├── candidate_intervention
 ├── expected_benefit
 ├── expected_risk
 ├── contraindications
 ├── response_estimate
 ├── uncertainty
 ├── model_version
 ├── evidence_version
 └── status
```

No intervention recommendation should be produced solely from a single cell score. Any future clinical/therapeutic layer requires independent scientific and clinical validation.

---

# 18. FRONTEND — missing structural layers

## 🔴 P0 — Real Cell Inspector

```text
frontend/digital-twin/inspectors/cell/
├── CellInspector
├── CellIdentity
├── CellMorphology
├── CellState
├── CellAge
├── CellEvidence
├── CellUncertainty
└── CellSource
```

Target view:

```text
CELL #A38291

[real cell image]

Identity
  Keratinocyte
  confidence 94%

Morphology
  Area       ...
  Nucleus    ...
  Shape      ...

State
  Stress       ...
  Senescence   ...
  Damage       ...

Age
  Estimated: ...
  Uncertainty: ...

Evidence
  WSI
  microscopy
  RNA

[View source]
```

The inspector must distinguish measured values from model-derived interpretations.

---

## 19. 🔴 Real WSI viewer

```text
frontend/digital-twin/viewers/wsi/
├── WSIViewer
├── TileViewport
├── ZoomController
├── ROISelector
├── SegmentationOverlay
├── CellSelector
├── CoordinateMapper
└── ScaleIndicator
```

Required capabilities:

```text
WSI
 ├── zoom
 ├── pan
 ├── multi-resolution tiles
 ├── ROI
 ├── segmentation overlay
 ├── cell selection
 └── coordinate mapping
```

The viewer should request the appropriate image resolution rather than loading an entire whole-slide image into the browser.

---

## 20. 🔴 Cell overlay on tissue

```text
frontend/digital-twin/overlays/segmentation/
├── CellOverlay
├── CellSelection
├── CellLabels
├── TissueBoundaries
└── OverlayLegend
```

Conceptually:

```text
tissue
 ├── cell 1
 ├── cell 2
 ├── cell 3
 ├── cell 4
 └── ...
```

Selection must resolve to a stable backend `cell_id`, not a visual placeholder such as `Cell target 3`.

---

## 21. 🔴 Evidence panel

```text
frontend/digital-twin/inspectors/evidence/
├── EvidencePanel
├── SourceViewer
├── MeasurementList
├── ModelInfo
├── Confidence
├── Provenance
└── EvidenceCoverage
```

```text
Result
 ↓
Why?
 ↓
Evidence
 ↓
Source image
 ↓
Measurement
 ↓
Model
 ↓
Confidence
 ↓
Provenance
```

Every AI-derived result should expose its supporting evidence and limitations.

---

## 22. 🔴 Timeline

```text
frontend/digital-twin/timeline/
├── Timeline
├── TimepointSelector
├── ObservationTimeline
├── CellTimeline
├── TissueTimeline
└── MacroTimeline
```

```text
2026 ───── 2028 ───── 2030 ───── 2035
  │          │          │          │
  T0         T1         T2         T3
```

The selected timepoint must synchronize with the hand, tissue, cellular, evidence, and analysis views.

---

## 23. 🔴 Comparison view

```text
frontend/digital-twin/views/comparison/
├── ComparisonView
├── MetricComparison
├── MorphologyComparison
├── StateComparison
├── AgeComparison
└── ChangeMap
```

Example:

```text
              T0             T1

Morphology    normal         altered
Senescence    low            elevated
Damage        low            medium
Age           47             53
```

The UI should show measured changes separately from inferred changes.

---

## 24. 🟠 Biological heatmap

```text
frontend/digital-twin/overlays/biological/
├── Heatmap
├── MetricSelector
├── ScaleLegend
├── RegionAggregation
└── UncertaintyOverlay
```

The heatmap must always be tied to an explicit metric, for example:

```text
senescence signal
```

rather than an undefined global `health` color.

---

## 25. 🟠 Multi-scale synchronized viewer

This is a core differentiator of the product.

```text
┌─────────────┐
│ 3D HAND     │
│      ●      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ TISSUE      │
│ █████████   │
│    ●        │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ CELLS       │
│ ○ ○ ● ○ ○   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ CELL        │
│    ◉        │
└─────────────┘
```

A selection at any level should propagate through the spatial hierarchy:

```text
Hand region
 ↕
Tissue
 ↕
ROI
 ↕
Cell
 ↕
Cell evidence
```

The synchronized viewer should be driven by real spatial registrations whenever evidence exists.

---

## 26. 🟠 “Why this conclusion?” UI

```text
frontend/digital-twin/inspectors/evidence/why/
```

Example:

```text
Why?

✓ Cell morphology
✓ Nuclear morphology
✓ Marker X
? RNA unavailable
? Longitudinal data unavailable

Confidence: medium
```

This is preferable to opaque output such as:

```text
AI says: OLD CELL
```

---

## 27. 🟠 Data quality indicators

```text
frontend/digital-twin/overlays/quality/
├── DataCoverage
├── QualityIndicator
├── ModalityCoverage
└── Applicability
```

```text
DATA COVERAGE

Macro       ██████████ 100%
Tissue      ███████░░░ 70%
Cellular    ████░░░░░░ 40%
Molecular   ██░░░░░░░░ 20%
```

Coverage should be computed from actual available evidence, not from UI navigation depth.

---

## 28. 🟡 Data-driven 3D model

Current conceptual direction:

```text
Three.js
 ↓
procedural hand
```

Target architecture:

```text
real anatomical model
 ↓
registered regions
 ↓
registered evidence
 ↓
registered tissue
 ↓
registered cells
```

The 3D model should become a spatial index into the twin rather than merely a visualization.

---

# 29. Target backend structure

```text
backend/
│
├── api/
│   ├── subjects/
│   ├── hands/
│   ├── observations/
│   ├── samples/
│   ├── spatial/
│   ├── tissues/
│   ├── cells/
│   ├── molecular/
│   ├── analyses/
│   ├── aging/
│   ├── pathology/
│   ├── longitudinal/
│   ├── evidence/
│   ├── reference/
│   └── interventions/
│
├── domain/
│   ├── subject/
│   ├── anatomy/
│   ├── spatial/
│   ├── cell/
│   ├── tissue/
│   ├── twin/
│   ├── reference/
│   └── intervention/
│
├── pipelines/
│   ├── ingestion/
│   ├── registration/
│   ├── segmentation/
│   ├── feature_extraction/
│   ├── cell_analysis/
│   ├── molecular/
│   └── fusion/
│
├── models/
│   ├── cell_state/
│   ├── aging/
│   ├── pathology/
│   └── prediction/
│
├── evidence/
├── provenance/
├── qc/
├── longitudinal/
├── reference/
├── intervention/
├── model_registry/
└── database/
```

This is a target separation of responsibilities, not a requirement to perform a large directory migration immediately.

---

# 30. Target frontend structure

```text
frontend/digital-twin/
│
├── views/
│   ├── hand/
│   ├── tissue/
│   ├── cellular/
│   ├── cell/
│   ├── timeline/
│   └── comparison/
│
├── viewers/
│   ├── hand-3d/
│   ├── wsi/
│   ├── microscopy/
│   └── cell/
│
├── inspectors/
│   ├── region/
│   ├── tissue/
│   ├── cell/
│   ├── evidence/
│   └── why/
│
├── overlays/
│   ├── segmentation/
│   ├── pathology/
│   ├── ageing/
│   ├── biological/
│   ├── quality/
│   └── uncertainty/
│
├── navigation/
├── timeline/
├── evidence/
├── state/
├── reference/
└── api/
```

## Implementation principle

Build the architecture around this chain:

```text
real observation
 ↓
registered sample
 ↓
registered tissue / ROI
 ↓
real cell
 ↓
measurements
 ↓
evidence
 ↓
validated model
 ↓
uncertainty
 ↓
longitudinal twin
```

Only after this chain is reliable should the system expose higher-level disease, ageing, or intervention interpretations.