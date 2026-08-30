# Target Backend / Frontend Structure

This document defines the target structural direction for the Hand Digital Twin. It is an architectural target, not a claim that every component is already implemented.

## 1. Target structure

Current high-level structure:

```text
Frontend
  └── 3D Hand
       └── Macro → Tissue → Cellular → Cell

Backend
  ├── ingestion
  ├── observations
  ├── assets
  ├── provenance
  ├── analysis
  └── twin
```

Target structure:

```text
                    DIGITAL TWIN
                         │
              ┌──────────┴──────────┐
              │                     │
          FRONTEND               BACKEND
              │                     │
       Visualization          Biological Model
              │                     │
       Spatial Navigation     Spatial Registry
              │                     │
       Evidence Viewer        Sample Management
              │                     │
       Cell Inspector         Cell Registry
              │                     │
       Analysis UI            Cell Segmentation
              │                     │
       Timeline               Cell Features
              │                     │
       Comparison             Cell State
                                    │
                              Cell Age Model
                                    │
                              Disease Model
                                    │
                              Uncertainty
                                    │
                              Longitudinal
                                    │
                              Intervention
```

The core architectural rule is that the frontend is a spatial and temporal view over evidence-backed biological entities. A visual representation must not be treated as biological evidence merely because the UI can navigate to a deeper level.

---

# 2. BACKEND — required structural elements

## 🔴 P0 — Person / Subject model

A formal subject model is required:

```text
Subject
 ├── demographics
 ├── baseline
 ├── hand(s)
 └── timepoints
```

Relationship:

```text
Subject
   ↓
Visit / Timepoint
   ↓
Observation
   ↓
Sample
```

This is the foundation for a true longitudinal twin.

## 🔴 P0 — Sample model

```text
Sample
 ├── subject_id
 ├── timepoint
 ├── anatomical_region
 ├── tissue
 ├── collection_method
 ├── preparation
 ├── source
 └── provenance
```

This layer is fundamental for connecting observations to tissue, WSI/microscopy and individual cells.

## 🔴 P0 — Spatial Registry

```text
Hand
 ↓
Region
 ↓
Tissue
 ↓
Sample
 ↓
Slide
 ↓
ROI
 ↓
Cell
```

Required coordinate transformations:

```text
hand_coordinates
      ↕
sample_coordinates
      ↕
slide_coordinates
      ↕
cell_coordinates
```

The registry must make spatial relationships explicit rather than relying on UI labels or heuristics.

---

# 3. 🔴 Cell Registry

```text
Cell
 ├── cell_id
 ├── sample_id
 ├── tissue_id
 ├── spatial_position
 ├── cell_type
 ├── segmentation
 ├── morphology
 ├── molecular_data
 ├── state
 ├── age_estimate
 ├── confidence
 └── provenance
```

`Cell ID` must be a stable biological/data identifier, not a presentation-only value such as `Cell target 3`.

---

# 4. 🔴 Cell segmentation pipeline

```text
WSI
 ↓
tiling
 ↓
preprocessing
 ↓
segmentation
 ↓
cell instances
 ↓
cell IDs
```

Candidate API surface:

```text
POST /api/cells/segment
GET  /api/cells
GET  /api/cells/{cell_id}
GET  /api/cells/{cell_id}/image
```

The implementation must preserve the link between segmentation output, source image/ROI and cell identity.

---

# 5. 🔴 Cell feature extraction

Every cell should eventually have measurable features:

```text
Morphology
 ├── area
 ├── perimeter
 ├── circularity
 ├── eccentricity
 ├── nucleus_area
 ├── nucleus/cytoplasm ratio
 └── shape descriptors
```

Potential molecular features:

```text
Molecular
 ├── gene expression
 ├── protein markers
 └── pathway activity
```

The backend should persist the underlying measurements, not only a model's final classification.

---

# 6. 🔴 Cell state model

Avoid reducing a cell to a binary `healthy / sick` label.

```text
CellState
 ├── healthy_probability
 ├── pathology_signals
 ├── stress
 ├── senescence
 ├── inflammation
 ├── damage
 ├── proliferation
 ├── metabolic_state
 └── uncertainty
```

The system must be able to return:

```text
INSUFFICIENT EVIDENCE
```

when the required evidence is unavailable.

---

# 7. 🔴 Biological age engine

Target module:

```text
aging/
```

Target flow:

```text
Cell
 ↓
biomarkers
 ↓
age model
 ↓
estimated biological age
 ↓
confidence interval
```

Example representation:

```text
estimated_age: 61
uncertainty: ±8
chronological_age: 52
```

An age estimate must always remain linked to the biomarkers, model/version, reference population and uncertainty that produced it.

---

# 8. 🔴 Disease / pathology engine

```text
cell
 ↓
features
 ↓
pathology models
 ↓
signals
 ↓
risk
```

Do not model this as simply:

```text
image → sick
```

Instead:

```text
observation
 → biomarker
 → abnormality
 → evidence
 → confidence
 → interpretation
```

---

# 9. 🔴 Evidence engine

Provenance should evolve into a formal evidence representation:

```text
Evidence
 ├── source
 ├── observation
 ├── measurement
 ├── model
 ├── model_version
 ├── quality
 ├── confidence
 ├── timestamp
 └── provenance
```

Every important result should be able to answer:

> Where did this conclusion come from?

---

# 10. 🔴 Uncertainty engine

The following should carry explicit uncertainty/quality metadata:

```text
measurement
prediction
age
health
 disease
```

with:

```text
confidence
uncertainty
data_quality
coverage
```

Missing evidence must not be silently converted into a negative finding.

---

# 11. 🔴 Longitudinal twin

```text
T0
 ↓
T1
 ↓
T2
 ↓
T3
```

The system should support comparisons such as:

```text
Cell population T0
        ↓
Cell population T1
        ↓
change
```

The twin should answer both:

> What is the current state?

and:

> How is the state changing over time?

---

# 12. 🔴 Cell lineage / tracking

Where the data permits it:

```text
Cell T0
   ↓
Cell T1
   ↓
Cell T2
```

Otherwise support population-level tracking:

```text
population-level tracking
```

This is important for studying cellular turnover, persistence and ageing trajectories.

---

# 13. 🟠 Multimodal fusion

Target module:

```text
fusion/
```

Inputs:

```text
macro imaging
+
microscopy
+
WSI
+
RNA
+
metadata
```

Fusion must use explicit subject/sample/time/spatial relationships, not accidental filename or UI heuristics.

---

# 14. 🟠 Quality Control

```text
QC
 ├── image quality
 ├── segmentation quality
 ├── sample quality
 ├── RNA quality
 ├── registration quality
 └── model applicability
```

A model should be able to decline interpretation when input quality or applicability is inadequate.

---

# 15. 🟠 Model registry

Every AI/analysis model should be versioned:

```text
Model
 ├── model_id
 ├── version
 ├── training_data
 ├── validation_data
 ├── intended_use
 ├── limitations
 └── metrics
```

Therefore:

```text
Cell age = 61
```

must be traceable to something such as:

```text
model = cell-age-v0.3
```

along with its evidence, reference population, calibration and uncertainty.

---

# Frontend additions required by the same architecture

The backend structure above implies the following frontend capabilities:

```text
frontend/digital-twin/
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
│   └── evidence/
│
├── overlays/
│   ├── segmentation/
│   ├── pathology/
│   ├── ageing/
│   └── uncertainty/
│
├── navigation/
├── timeline/
├── evidence/
├── state/
└── api/
```

The most important frontend principle is:

```text
3D region
   ↓
real registered evidence
   ↓
real tissue/ROI
   ↓
real segmented cell
   ↓
real cell measurements
```

A procedural visualization or navigation target must never be presented as if it were a measured biological object.

---

# Implementation priority

### P0 — establish the biological/spatial spine

1. Subject / Timepoint
2. Sample model
3. Spatial Registry
4. Stable Cell ID
5. Real cell segmentation
6. Cell ↔ tissue ↔ hand registration
7. Real Cell Inspector
8. WSI/microscopy viewer
9. Evidence/provenance chain
10. Measurement model

### P1 — biological intelligence

11. Cell morphology
12. Cell identity
13. Cell state
14. QC
15. Uncertainty
16. Longitudinal tracking
17. Multimodal fusion
18. Reference population
19. Biological-age model
20. Pathology models

### P2 — future decision-support layer

21. Risk estimation
22. Intervention modeling
23. Treatment response
24. Rejuvenation modeling
25. Decision support

This roadmap deliberately puts evidence, measurement and spatial identity before health scores, biological age and intervention recommendations.
