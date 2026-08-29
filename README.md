# testHP

## Human Pathology Platform — research prototype

`testHP` is a research-oriented platform for monitoring and analysing human biological state from multimodal evidence. The project has two complementary goals:

1. **Longitudinal monitoring** — follow biological observations over time and detect changes, trends, anomalies and uncertainty.
2. **Current-state assessment** — analyse newly uploaded observations even when there is no previous history, using only the evidence that is actually available.

The long-term vision is a hierarchical digital biological twin connecting evidence from macro anatomy through tissue, cellular and molecular levels while preserving provenance, uncertainty and evidence boundaries.

> **Vision:** treat the human body as a dynamic biological system rather than reducing health to one score or one diagnosis.

The software is a **research prototype**. It is not a diagnostic system, medical device, autonomous clinical decision system, or clinically validated biological-age calculator.

---

## Current user-facing application

The repository currently contains two related browser experiences:

- `web/` — the general research/data-ingestion dashboard.
- `frontend/digital-twin/` — the **Hand Digital Twin** workspace served at:

```text
http://127.0.0.1:8000/digital-twin
```

The Hand Digital Twin is currently the main interactive spatial interface. It combines:

- an interactive Three.js hand viewport,
- progressive spatial navigation,
- macro → tissue → cellular → single-cell navigation,
- breadcrumb navigation back to higher spatial levels,
- region inspection and evidence availability,
- macro image evidence previews,
- spatial evidence/preview endpoints,
- research-level biological-state placeholders,
- a longitudinal observation timeline primitive,
- observation/file upload through FastAPI,
- a Twin-Viewport debug panel for renderer and navigation state.

The key interaction is **spatial drill-down**: selecting a deeper target changes the Twin-Viewport representation instead of merely changing a label. Moving back up restores the parent spatial level.

Example:

```text
Hand
  ↓
Ring finger
  ↓
Middle segment
  ↓
Microscopy field B
  ↓
Cell target 3
```

---

## Spatial resolution model

The current spatial navigation model uses four resolutions:

```text
MACRO ANATOMY
    ↓
TISSUE FIELD
    ↓
CELLULAR FIELD
    ↓
SINGLE CELL
```

The navigation state is effectively:

```text
selectedSpatialNode
        ↓
spatial path + resolution
        ↓
Twin-Viewport renderer
```

Conceptually the renderer selection is:

```text
macro    → Hand3DRenderer / DeepRenderer

tissue   → Tissue / deep spatial renderer

cellular → Cellular-field renderer

cell     → Single-cell renderer
```

The important architectural rule is that **one Twin-Viewport represents the currently selected spatial node**. A deeper target does not automatically inherit biological evidence from its parent.

The current digital-twin frontend contains shared spatial infrastructure such as:

```text
frontend/digital-twin/
├── index.html
├── app.js
├── spatial-layer-viewport.js
├── spatial-evidence-renderer.js
├── spatial-viewport-debug.js
├── spatial-navigation-v2.js
├── layer-selector.js
└── layer-visualization-selector.js
```

---

## Evidence and uploads

The FastAPI backend currently exposes, among others:

```text
GET  /api/hand/analysis
GET  /api/hand/twin
GET  /api/spatial/evidence/{asset_id}
GET  /api/spatial/preview/{asset_id}
GET  /api/hand/evidence/{asset_id}
POST /api/hand/validate
POST /api/upload/{modality}
```

Supported upload modalities currently include:

```text
hand | video | images | wsi | rna | metadata
```

Uploaded observations retain an asset identifier and provenance information. Large local datasets should not be committed to Git; the application reads configured local data at runtime.

The next intended extension is **spatial evidence attachment**: select a precise node in the Twin-Viewport and attach an image or other observation directly to that node, for example:

```text
Hand → Ring finger → Middle segment → Microscopy field B
```

The existing upload and evidence infrastructure provides the foundation for this workflow.

---

## Current-state assessment vs longitudinal monitoring

These are deliberately separate workflows.

### Current-state assessment

A user can provide present observations without any previous history. The system should analyse only the available evidence and expose:

```text
observed evidence
available modalities
quality / uncertainty
spatial coverage
possible biological signals
insufficient evidence
recommended next measurement
```

It must not invent a historical baseline when none exists.

### Longitudinal monitoring

When observations exist at multiple timepoints, the system can compare them as:

```text
baseline → intermediate observations → latest state
```

This enables trajectory analysis, trend detection, change-point detection, multimodal disagreement analysis and monitoring of intervention-related changes.

---

## Biological interpretation by layer

The intended system should eventually provide a research summary appropriate to each selected layer:

```text
MACRO
  → structural / anatomical summary

TISSUE
  → tissue morphology / tissue-state summary

CELLULAR
  → cellular composition, morphology and cellular-state summary

SINGLE CELL
  → cell-level state, health-related indicators and biological-age research signals

MOLECULAR
  → molecular measurements and molecular-state summary
```

These summaries must remain evidence-linked. A deeper spatial target does not imply that deeper biological evidence exists there.

When evidence is insufficient, the correct output is explicitly:

```text
INSUFFICIENT EVIDENCE
```

rather than an unsupported biological conclusion.

---

## Cell Health State

The intended cell-level representation is not a binary `healthy / unhealthy` label. A single cell should eventually be represented as a **multidimensional biological state**, combining observations, measured features, derived indicators, research-level inferences and explicit uncertainty.

A proposed target model is:

```text
CELL
│
├── identity
│   ├── cell type
│   ├── subtype
│   └── identity confidence
│
├── morphology
│   ├── size
│   ├── shape
│   ├── nuclear features
│   └── structural abnormalities
│
├── viability
│   ├── viable / non-viable
│   └── viability indicators
│
├── cellular stress
│   ├── oxidative stress
│   ├── ER stress
│   └── general stress signals
│
├── senescence
│   ├── senescence indicators
│   ├── senescence-associated phenotype
│   └── confidence
│
├── DNA / genome state
│   ├── DNA damage indicators
│   ├── genomic instability
│   └── repair-related signals
│
├── mitochondrial state
│   ├── mitochondrial morphology
│   ├── activity
│   └── dysfunction indicators
│
├── inflammatory state
│   ├── inflammatory signals
│   └── immune-related signals
│
├── metabolic state
│   ├── metabolic activity
│   └── metabolic abnormalities
│
├── proteostasis
│   ├── protein homeostasis
│   ├── aggregation indicators
│   └── degradation / clearance signals
│
├── epigenetic state
│   ├── epigenetic markers
│   ├── methylation-related signals
│   └── chromatin-related signals
│
├── proliferation / cell cycle
│   ├── proliferation state
│   ├── cell-cycle state
│   └── abnormal proliferation indicators
│
├── differentiation
│   ├── differentiation state
│   └── dedifferentiation indicators
│
├── pathology signals
│   ├── abnormal morphology
│   ├── disease-associated signals
│   └── other pathological indicators
│
├── biological age
│   ├── age-related biomarkers
│   ├── estimated biological age
│   ├── deviation from reference
│   └── age-estimation confidence
│
└── uncertainty
    ├── measurement quality
    ├── evidence coverage
    ├── model confidence
    └── unresolved / insufficient evidence
```

### Evidence semantics

Not every cell will have every measurement. The system must distinguish between what was observed, measured, derived, inferred and simply unknown:

```text
OBSERVED
   ↓
MEASURED
   ↓
DERIVED
   ↓
INFERRED
   ↓
INSUFFICIENT EVIDENCE
```

For example, absence of a DNA-damage measurement must not be interpreted as absence of DNA damage:

```text
DNA damage
    ↓
no appropriate measurement available
    ↓
not equivalent to "no damage"
    ↓
INSUFFICIENT EVIDENCE
```

Likewise, biological age should be represented as an estimate tied to the biomarkers, model and uncertainty that produced it, rather than as an unexplained number.

### Target Cell Health State

The eventual research-level state can be organised into:

```text
CELL HEALTH STATE
│
├── structural state
├── functional state
├── stress state
├── damage state
├── repair state
├── inflammatory state
├── metabolic state
├── senescence state
├── proliferative state
├── pathological signals
├── biological-age-related signals
└── confidence / uncertainty
```

Only after appropriate scientific validation should the system derive simplified categories such as:

```text
healthy
stable
stressed
senescent-like
damaged
pathology-associated
uncertain
```

These categories must not replace the underlying evidence profile.

### Current status

The repository contains foundations for this capability, including cellular-analysis components, multimodal ingestion, WSI/microscopy support, molecular-data support, provenance, uncertainty and hierarchical spatial representation. However, it does **not yet provide a scientifically validated, multimodal cell-level health assessment system**.

In particular, the project does not yet establish that a specific cell can reliably be assigned a health state, pathology state or biological age from available evidence. That requires dedicated models, reference datasets, calibration, reproducibility testing and independent scientific validation.

---

## Biological ageing

Ageing is treated as a multidimensional research problem rather than one universal number:

```text
Cellular | Tissue | Immune | Vascular | Skeletal
Neural   | Metabolic | Molecular | Functional
```

The project focuses on trajectories and rates of change. It does **not currently contain a clinically validated biological-age clock**.

The intended framework distinguishes:

```text
normal variation
      vs
measurement artefact
      vs
age-associated change
      vs
pathological signal
      vs
intervention response
      vs
insufficient evidence
```

---

## Digital Biological Twin

The long-term objective is an evolving computational representation of an individual's biological state:

```text
                 DIGITAL BIOLOGICAL TWIN
                           |
        +------------------+------------------+
        |                  |                  |
      organs             tissues            cells
        |                  |                  |
     function           morphology          state
        +------------------+------------------+
                           |
                    molecular state
                           |
                    ageing trajectories
                           |
                    disease/risk signals
                           |
                     interventions
                           |
                       uncertainty
```

The repository already contains the digital-twin data-model and observation-to-twin foundations, together with an interactive hand-focused digital-twin interface. A complete predictive or mechanistic whole-body digital twin is **not yet implemented**.

---

## Current architecture

```text
core/          biological data, measurements, anatomy, quality
analysis/      anomalies, trends, change points, ageing analysis
segmentation/  cell segmentation baseline
pipelines/     tissue and cell analysis
pipeline/      additional modality pipelines
integration/   observation → digital twin
organism/      organism state and biological twin
longitudinal/  trajectory components
aging/         ageing trajectories and pathology framework
monitoring/    longitudinal monitoring cycles
intervention/  efficacy/safety surveillance
planning/      additional measurement planning
validation/    validation metrics and prospective research
audit/         evidence-linked decision records
visualization/ research visualization primitives
backend/       FastAPI API, ingestion, evidence and hand-twin services
frontend/      digital-twin user interface
web/           general research/data dashboard
digital_twin/  digital-twin update and temporal-state components
datasets/      dataset definitions and registries
configs/       dataset and hand-spatial configuration
docs/          research/data/interface contracts and stage documentation
tests/         automated tests
```

The architecture deliberately separates **observation, analysis, inference, intervention surveillance and decision/audit**.

---

## Integrated research flow

```text
CURRENT OR LONGITUDINAL OBSERVATIONS
                ↓
       QUALITY / UNCERTAINTY
                ↓
          MODALITY ANALYSIS
                ↓
         MULTIMODAL FUSION
                ↓
      HIERARCHICAL BIOLOGICAL STATE
                ↓
         DIGITAL BIOLOGICAL TWIN
                ↓
       SPATIAL / TEMPORAL VIEW
          ↙             ↘
   CURRENT STATE     LONGITUDINAL
     ASSESSMENT        ANALYSIS
          ↓             ↓
       SIGNALS       TRENDS / CHANGE
          \             /
           ↓           ↓
       UNCERTAINTY / DISAGREEMENT
                    ↓
          MEASUREMENT PLANNING
                    ↓
         INTERVENTION SURVEILLANCE
                    ↓
               VALIDATION
                    ↓
              DECISION + AUDIT
                    ↓
              UPDATED TWIN
                    ↓
             NEXT OBSERVATION
```

---

## Development stages completed

Stages **1–30** established the biological monitoring and research architecture:

- **Stages 1–15:** biological monitoring foundation, data models, cell analysis, organs, organism state, ageing and longitudinal monitoring.
- **Stage 16:** unified multimodal observation layer.
- **Stage 17:** measurement quality and uncertainty.
- **Stage 18:** multimodal fusion.
- **Stage 19:** hierarchical biological state.
- **Stage 20:** Digital Biological Twin data-model foundation.
- **Stage 21:** advanced anomaly detection.
- **Stage 22:** longitudinal biological change analysis.
- **Stage 23:** intervention surveillance.
- **Stage 24:** validation framework.
- **Stage 25:** unified observation-to-twin pipeline.
- **Stage 26:** temporal change-point detection.
- **Stage 27:** multimodal disagreement and measurement planning.
- **Stage 28:** ageing versus pathology framework.
- **Stage 29:** prospective validation infrastructure.
- **Stage 30:** research decision and audit layer.

The repository has since moved beyond the purely backend/data-model stages into an **interactive Hand Digital Twin / spatial research interface**. This UI work is the current product-integration phase; it does not mean that the complete scientific system is finished.

---

## Validation and scientific status

The repository contains validation and testing primitives, but scientific validation remains future work:

```text
unit tests
   ↓
integration tests
   ↓
benchmark datasets
   ↓
external validation
   ↓
longitudinal cohorts
   ↓
prospective studies
   ↓
clinical validation
   ↓
regulatory / safety assessment
```

Performance must eventually be evaluated across populations, modalities, anatomical regions, diseases and measurement conditions. Reproducibility, calibration, provenance, uncertainty and subgroup performance are essential.

A retrospective numerical metric is not proof of clinical utility.

---

## Safety and decision philosophy

1. **Observation is not diagnosis.**
2. **A risk score is not a medical decision.**
3. **Uncertainty must be represented rather than hidden.**
4. **Conflicting measurements should trigger investigation, not arbitrary averaging.**
5. **Intervention benefit must be monitored separately from safety.**
6. **Automated outputs require appropriate human and clinical oversight before clinical use.**
7. **Insufficient evidence is a valid outcome.**
8. **Important decisions should retain evidence, model/version information and an audit trail.**
9. **Deeper spatial navigation must not be mistaken for deeper biological evidence.**

The current decision layer is research-level decision support, not an autonomous medical decision system.

---

## Development roadmap

The next phase should prioritize the actual research workflow rather than simply adding more scores.

### 1. Spatial evidence attachment

Allow the user to select a precise spatial node in the Twin-Viewport and upload/attach an image or other evidence directly to that node.

### 2. Layer-specific biological summaries

Provide research summaries appropriate to the selected layer, from macro anatomy through tissue and cellular levels, without inheriting unsupported evidence from parent nodes.

### 3. Current-state analysis

Support a dedicated workflow for analysing a present-day dataset with no historical observations.

### 4. Longitudinal monitoring

Connect repeated observations to the same spatial/anatomical entities and display biological changes through time.

### 5. Cellular assessment

Develop validated cellular analysis capable of estimating research-level cell-state/health indicators and, where scientifically justified, biological-age-related signals.

### 6. Multimodal evidence fusion

Link macro images, WSI/microscopy, cellular data and molecular measurements through explicit subject/timepoint/spatial identifiers and provenance.

### 7. Validation and reproducibility

Expand deterministic fixtures, benchmark datasets, calibration, uncertainty evaluation, external replication and prospective studies.

### 8. Predictive digital twin

Only after reliable data and validation foundations are established, add predictive biological models and mechanistic hypotheses.

---

## Running locally

From the repository root:

```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/digital-twin
http://127.0.0.1:8000/docs
```

The FastAPI upload endpoints require `python-multipart` in the environment.

Large local datasets should not be committed to Git; they are read from configured runtime data directories.

---

## Important limitations

`testHP` is currently a **research prototype**. It should not be used to diagnose disease, prescribe treatment, determine biological age for medical purposes, or make autonomous clinical decisions.

A complete predictive digital biological twin, clinically validated ageing models, clinically validated multimodal fusion, validated intervention monitoring, validated cell-health assessment and clinical decision support are **not yet implemented**.

The long-term lifespan/rejuvenation objectives are research goals, not demonstrated outcomes of the software.

---

## Project status

**Current status: interactive Hand Digital Twin and progressive spatial-navigation prototype built on top of the Stage 1–30 research architecture.**

The project can now represent paths from macro anatomy to tissue fields, microscopy fields and single-cell targets, navigate back to higher spatial layers, inspect linked evidence and expose Twin-Viewport state during development.

The most important next step is to turn spatial navigation into a true **evidence attachment and analysis workflow**, so uploaded observations become explicitly associated with the selected anatomical/spatial node and can subsequently feed both current-state assessment and longitudinal monitoring.

```text
select spatial node
        ↓
attach evidence
        ↓
validate + preserve provenance
        ↓
analyse at the appropriate resolution
        ↓
summarise evidence / uncertainty
        ↓
update current biological state
        ↓
optionally compare with previous observations
        ↓
update longitudinal twin history
        ↓
plan next measurement when evidence is insufficient
```

The ultimate goal remains a platform that can continuously construct and update a **computational representation of human biological state**, enabling research into long-term health, ageing, disease prevention and biological rejuvenation.
