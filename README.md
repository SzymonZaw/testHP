# testHP

## Human Pathology Platform — research prototype

`testHP` is a research-oriented platform for building a multimodal, longitudinal model of human biological state. The long-term vision is to monitor the organism at multiple biological levels, detect abnormalities and ageing-related changes, understand how they evolve, and eventually evaluate interventions that preserve or restore biological function.

> **Vision:** treat the human body as a dynamic biological system rather than reducing health to one score or one diagnosis.

The software is a research prototype and is not a diagnostic or autonomous clinical decision system.

---

## User-facing platform

The repository now includes a lightweight browser dashboard in `web/` and a FastAPI service in `backend/app.py`.

The dashboard is designed for a **research user**, rather than only a developer. It presents:

- what datasets entered the run,
- which modalities are represented,
- how many supported files were found,
- a visual pipeline from **Input → Ingestion → Validation → Normalization → Multimodal Fusion → Research View**,
- dataset-level warnings and unavailable inputs,
- an evidence boundary and next research action,
- an interactive dataset explorer.

Large local datasets do not need to be committed to GitHub. The application reads the local `data/raw` tree at runtime and reports missing or unavailable datasets explicitly. This is especially important for datasets such as **SCIN**, where repository metadata can be present without the full image collection.

### Start the dashboard

From the repository root:

```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
```

Developer documentation remains available at `/docs`.

### Evidence boundary

The dashboard deliberately does **not** turn file presence into a medical conclusion. It currently reports dataset-level evidence and pipeline readiness. Subject-level multimodal links are only counted when an explicit shared identifier exists. Biological inference should be added only when the corresponding modality adapter/model and validation evidence are available.

---

## Current architecture

Stages 1–30 establish the biological monitoring foundation, multimodal analysis, longitudinal modelling, digital-twin history, intervention surveillance, validation, integration, measurement planning and audit primitives.

```text
core/          biological data, measurements, anatomy, quality
analysis/      anomalies, trends, change points
segmentation/  cell segmentation baseline
pipelines/     cell analysis
integration/   observation -> digital twin
organs/        organ models and signal propagation
organism/      organism state and digital biological twin
longitudinal/  trajectory components
aging/         ageing trajectories and ageing/pathology framework
monitoring/    longitudinal monitoring cycles
intervention/  efficacy/safety surveillance
planning/      additional measurement planning
validation/    validation metrics and prospective research
audit/         evidence-linked decision records
visualization/ research visualization primitives
backend/       user-facing API and pipeline dashboard
web/           user-facing browser dashboard
tests/         automated tests for implemented components
```

The architecture deliberately separates **observation, inference, intervention surveillance and decision/audit**.

---

## Integrated flow

```text
MULTIMODAL OBSERVATIONS
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
 ┌────────┴────────┐
 ↓                 ↓
ANOMALY       LONGITUDINAL
DETECTION       ANALYSIS
 └────────┬────────┘
          ↓
   CHANGE-POINT ANALYSIS
          ↓
 MULTIMODAL DISAGREEMENT
          ↓
 MEASUREMENT PLANNING
          ↓
INTERVENTION SURVEILLANCE
      ↙          ↘
 efficacy       safety
      \          /
       ↓        ↓
        VALIDATION
             ↓
       DECISION + AUDIT
             ↓
        UPDATED TWIN
             ↓
      NEXT MEASUREMENT
```

The system should be able to return **insufficient evidence** rather than forcing an unjustified conclusion.

---

## Development stages completed

### Stages 1–15 — Biological monitoring foundation

Established the common biological data model, cell-analysis baseline, organ representation and dependency graph, anomaly/risk foundations, ageing concepts, intervention analysis, whole-body organism state and continuous longitudinal monitoring.

### Stage 16 — Unified multimodal observation layer

Introduced common representations for observations from different modalities with measurement provenance and quality metadata.

### Stage 17 — Measurement quality and uncertainty

Added quality-aware handling so unreliable observations can be excluded or represented as insufficient evidence.

### Stage 18 — Multimodal fusion

Added quality-weighted fusion primitives while retaining modality provenance.

### Stage 19 — Hierarchical biological state

Added `core/hierarchy.py` connecting organism, system, organ, tissue, cell-population, cell and site levels.

### Stage 20 — Digital Biological Twin foundation

Added `organism/digital_twin.py` with longitudinal `TwinSnapshot` objects and persistent twin history. This is a data-model foundation, not a complete predictive twin.

### Stage 21 — Advanced anomaly detection

Added `analysis/advanced_anomaly.py` with transparent anomaly scoring, quality thresholds and explicit insufficient-evidence handling.

### Stage 22 — Longitudinal biological change analysis

Added `analysis/longitudinal.py` for repeated measurements, trend direction, slope, baseline-to-latest change and quality filtering.

### Stage 23 — Intervention surveillance

Added `intervention/surveillance.py` and tests for separate efficacy and safety trajectories. This is a research monitoring primitive, not a treatment recommendation system.

### Stage 24 — Validation framework

Added `validation/framework.py` and tests for MAE, RMSE, bias, quality filtering and subgroup evaluation. This is not clinical validation.

### Stage 25 — Unified observation-to-twin pipeline

Added `integration/observation_to_twin.py` and tests. Quality-filtered observations can now become `TwinSnapshot` objects and enter `DigitalBiologicalTwin` history while retaining modality provenance.

### Stage 26 — Temporal change-point detection

Added `analysis/change_points.py` to identify possible changes in longitudinal trajectory rather than treating every observation independently.

### Stage 27 — Multimodal disagreement and measurement planning

Added `planning/measurement_planner.py` for transparent suggestions of additional modalities when evidence is incomplete or conflicting. It is not autonomous clinical ordering.

### Stage 28 — Ageing versus pathology framework

Added `aging/pathology_framework.py` to represent normal variation, age-associated change, pathology signal, intervention response and insufficient evidence.

### Stage 29 — Prospective validation infrastructure

Added `validation/prospective.py` with cohort, experiment, dataset/model-version and audit primitives for reproducible prospective research.

### Stage 30 — Research decision and audit layer

Added `audit/decision.py` with evidence references, auditable decision records and explicit research-level outcomes such as `measure_again`, `request_modality`, `expert_review`, `insufficient_evidence` and `continue_monitoring`.

---

## Biological ageing

Ageing should be represented by multiple dimensions rather than one universal clock:

```text
Cellular | Tissue | Immune | Vascular | Skeletal
Neural   | Metabolic | Molecular | Functional
```

The project focuses on trajectories and rates of change rather than treating a single biological-age number as ground truth. It does **not** currently contain a clinically validated biological-age clock.

The ageing/pathology layer is intended to distinguish:

```text
normal variation
      vs
measurement artefact
      vs
age-associated change
      vs
pathological change
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

Stage 25 provides the observation-to-snapshot ingestion path. A complete predictive or mechanistic digital twin is **not yet implemented**.

---

## Intervention and rejuvenation research

A long-term research direction is monitoring interventions intended to preserve or restore biological function. Partial cellular reprogramming involving **Yamanaka factors** is an example that illustrates why efficacy and safety must be monitored separately.

Potential rejuvenation effects would need to be evaluated alongside risks such as loss of cell identity, abnormal proliferation and tumour formation. The current software only provides research monitoring primitives; it does not implement, select or recommend a rejuvenation therapy.

---

## Measurement planning and uncertainty

A central design principle is:

> **When evidence is inadequate, the system should seek better evidence rather than invent certainty.**

If modalities disagree or uncertainty is high, the planning layer can represent a request for another measurement. This remains a research planning capability and is deliberately separated from autonomous clinical ordering.

---

## Validation

Stages 24 and 29 establish validation infrastructure, but scientific validation remains a future task:

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

Performance must eventually be assessed across populations, modalities, anatomical regions, diseases and measurement conditions. Reproducibility, calibration, provenance and subgroup performance are essential.

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

The current decision layer is research-level decision support, not an autonomous medical decision system.

---

## Future roadmap — Stage 31+

The first 30 architectural stages are represented in the repository. The next phase should prioritize **correctness, execution, reproducibility, data governance and scientific testing** rather than simply adding more scores.

### Stage 31 — End-to-end integration tests

Exercise the complete observation → quality → analysis → twin → validation → audit path with deterministic fixtures.

### Stage 32 — Data schemas and provenance contracts

Formalize identifiers, units, timestamps, anatomical locations, dataset versions, model versions and provenance requirements.

### Stage 33 — Reproducible research runner

Create versioned experiment configurations, deterministic runs, result manifests and machine-readable reports.

### Stage 34 — Governed multimodal datasets

Introduce public/research datasets and modality adapters while keeping sensitive human data out of source control.

### Stage 35 — Calibration and uncertainty evaluation

Evaluate calibration, uncertainty behaviour and failure modes rather than relying only on aggregate accuracy metrics.

### Stage 36 — Mechanistic and predictive modelling

Only after reliable data and validation foundations are established, add predictive biological models and mechanistic hypotheses.

### Stage 37+ — Scientific validation and translation

Progress through external replication, prospective research and, where appropriate, clinical/regulatory evaluation.

---

## Important limitations

`testHP` is currently a **research prototype**. It should not be used to diagnose disease, prescribe treatment, determine biological age for medical purposes, or make autonomous clinical decisions.

A complete predictive digital biological twin, clinically validated ageing models, clinically validated multimodal fusion, validated intervention monitoring and clinical decision support are **not yet implemented**.

The 200-year lifespan objective is a long-term research vision, not a demonstrated outcome of the software.

---

## Project status

**Current stage: Stage 30 — research decision and audit layer implemented; early research prototype.**

Stages 1–30 establish a path from multimodal observations through quality assessment, fusion, hierarchical state, longitudinal modelling, anomaly/change detection, measurement planning, intervention surveillance, validation and auditable research decisions.

Immediate priorities are **integration, correctness, testing, reproducibility, data governance and scientific validation**.

```text
measure
  -> validate quality
  -> analyse
  -> integrate
  -> update biological state
  -> detect abnormalities and change
  -> quantify uncertainty/conflicts
  -> choose additional measurement when justified
  -> monitor interventions separately
  -> validate outputs
  -> record evidence and provenance
  -> update the twin
  -> repeat
```

The ultimate goal is a platform that can continuously construct and update a **computational representation of human biological state**, enabling research into long-term health, ageing, disease prevention and biological rejuvenation.
