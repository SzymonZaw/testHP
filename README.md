# testHP

## Multimodal Biological Monitoring & Research Platform

`testHP` is a research-oriented platform for ingesting, validating, preprocessing and integrating multimodal biological data. Its long-term goal is to build an evolving computational representation of human biological state and study ageing, pathology, longitudinal change and intervention response.

> **Research principle:** when the available evidence is inadequate, the system should report insufficient evidence rather than invent certainty.

This repository is a research prototype. It is **not** a clinically validated diagnostic or treatment system.

---

## Current status

The current implementation contains a working research pipeline covering stages **1–10**:

```text
raw data
   ↓
1. ingestion & validation
   ↓
2. normalization & preprocessing
   ↓
3. multimodal fusion
   ↓
4. quality & uncertainty
   ↓
5. hierarchical biological state
   ↓
6. digital biological twin
   ↓
7. anomaly & longitudinal analysis
   ↓
8. evaluation
   ↓
9. research decision support
   ↓
10. audit & provenance
```

The implementation is intentionally conservative: public datasets are not assumed to represent the same person, and the system does not fabricate cross-dataset patient identities or longitudinal timepoints.

Stages 1–10 are an engineering/research foundation. They do **not** constitute clinical validation or a complete predictive digital twin.

---

## Repository structure

```text
testHP/
├── backend/             FastAPI application and API service
├── core/                common biological data structures and quality logic
├── datasets/            dataset registry, adapters and normalization
├── analysis/            anomaly and longitudinal analysis
├── evaluation/          pipeline readiness/evaluation
├── decision/            research-level decision support
├── audit/               provenance and run auditing
├── organism/            biological hierarchy / digital twin components
├── integration/         observation-to-twin integration
├── aging/               ageing/pathology research primitives
├── intervention/        intervention surveillance primitives
├── planning/            measurement-planning primitives
├── validation/          research validation utilities
├── tests/               automated tests and deterministic fixtures
├── scripts/             local demo/integration scripts
├── data/
│   └── raw/             local source datasets (large data is not committed)
├── .github/workflows/   GitHub Actions CI
├── requirements.txt     Python dependencies
└── README.md
```

The exact set of modules may evolve as the research architecture develops. The README describes the currently supported execution path rather than claiming future functionality.

---

## Python version

The project targets **CPython 3.14** for local development and CI.

PyTorch 2.10 or newer is required by the current dependency set because Python 3.14 support was added in the PyTorch 2.10 release line. citeturn0search1

Check your interpreter before installing dependencies:

```powershell
python --version
```

It should report Python 3.14.x.

---

## Raw data

Large datasets belong under:

```text
data/raw/
```

The raw directory is treated as **source data**. Dataset-specific loaders/adapters should interpret it without modifying the original source files.

Do **not** commit the full research datasets to GitHub. The repository should contain only small deterministic fixtures/examples required for tests and development.

Typical supported source families include image, WSI, RNA and hand/pose data. The exact directories available on a particular machine can be inspected through the API or dataset registry.

---

## Running locally

Create a Python 3.14 virtual environment and install dependencies:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then verify the interpreter and core dependencies:

```powershell
python --version
python -c "import torch; print(torch.__version__)"
```

Run the complete Python test suite from the repository root:

```powershell
python -m pytest -q
```

Run the demonstration/integration script:

```powershell
python scripts/run_demo.py
```

### FastAPI

If the `backend/` package is present in your checkout, start the API from the repository root with:

```powershell
python -m uvicorn backend.main:app --reload
```

The API is then available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Basic health check:

```text
GET /api/health
```

Project/data status:

```text
GET /api/status
```

Dataset inventory:

```text
GET /api/datasets
```

Pipeline description/validation:

```text
GET  /api/pipeline
POST /api/pipeline/validate
```

Pipeline execution:

```text
POST /api/run
```

The API currently performs a non-destructive research ingestion/integration path. It does not claim to perform clinical diagnosis or validated biological inference.

---

## Tests

Run the complete Python test suite from the repository root:

```bash
python -m pytest -q
```

Run the demonstration/integration script:

```bash
python scripts/run_demo.py
```

The test suite is designed to work with small fixtures and does not require the full multi-gigabyte research datasets.

---

## GitHub Actions CI

`.github/workflows/main.yml` checks three areas:

```text
Backend tests
     ↓
FastAPI startup / smoke test
     ↓
Frontend build (when the frontend package is present)
     ↓
CI gate
```

CI runs the Python jobs on **CPython 3.14** and uses the same full dependency set from `requirements-ci.txt` for backend and API validation.

CI also runs on pushes to `main` and `agent/**` branches and on pull requests targeting `main`.

The CI environment must remain independent of the large datasets in `data/raw/`; deterministic repository fixtures are used instead.

---

## Web framework

The backend is implemented with **FastAPI**. The repository is being prepared for a browser-based research interface, but documentation must not imply that a React frontend is production-ready unless its source and build configuration are actually present in the branch.

The current API already exposes the core operations needed by a future UI:

```text
status → dataset inventory → pipeline validation → pipeline execution
```

---

## Stages 1–10

### Stage 1 — Ingestion & validation

Discovers the available raw datasets and validates filesystem-level properties such as existence, supported formats, empty files and basic input integrity.

### Stage 2 — Normalization & preprocessing

Dataset-specific adapters convert source data into common normalized observations while retaining source paths and provenance. Preprocessing is deliberately modality-aware.

### Stage 3 — Multimodal fusion

Combines normalized observations from available modalities without inventing relationships between unrelated people or datasets.

### Stage 4 — Quality & uncertainty

Quality metadata and evidence limitations propagate through the pipeline. Low-quality or incomplete evidence can be rejected or marked insufficient.

### Stage 5 — Hierarchical biological state

Represents biological state across levels such as organism, system, organ, tissue, cell population, cell and anatomical site where the available evidence supports those levels.

### Stage 6 — Digital Biological Twin

Creates longitudinal snapshot primitives and retains observation provenance. This is a data-model foundation, **not a complete predictive/mechanistic digital twin**.

### Stage 7 — Anomaly & longitudinal analysis

Supports transparent anomaly and repeated-measurement analysis. A single observation is not treated as evidence of a longitudinal trend.

### Stage 8 — Evaluation

Evaluates pipeline readiness, available modalities, completeness and known limitations. This is engineering/research evaluation, not clinical validation.

### Stage 9 — Research decision support

Propagates evidence, uncertainty and research-level outcomes such as insufficient evidence or need for additional measurement. It is not an autonomous clinical decision system.

### Stage 10 — Audit & provenance

Records run identifiers, timestamps, dataset/source information, pipeline status and provenance so that research results can be inspected and reproduced.

---

## Scientific scope

The long-term research direction includes:

- multimodal characterization of human biological state,
- ageing trajectories,
- pathology-related changes,
- longitudinal monitoring,
- intervention efficacy and safety surveillance,
- multimodal disagreement and uncertainty,
- research-oriented digital biological twins.

Ageing should be treated as multidimensional rather than reduced to a single universal number. Potential dimensions include cellular, tissue, immune, vascular, skeletal, neural, metabolic, molecular and functional state.

The project does **not currently contain a clinically validated biological-age clock**.

---

## Data governance and provenance

Human biological datasets can contain sensitive information. Large source datasets should remain outside version control unless their license and governance explicitly permit redistribution.

Every modality adapter should preserve, where available:

- source dataset,
- source file/path or identifier,
- dataset version,
- observation timestamp,
- anatomical/site information,
- quality metadata,
- model/preprocessing version.

The platform must not manufacture patient identity links merely because two datasets describe similar biology.

---

## Validation roadmap

The current tests establish software correctness and pipeline behaviour. Scientific validation is a separate task:

```text
unit tests
   ↓
integration tests
   ↓
benchmark datasets
   ↓
external replication
   ↓
longitudinal cohorts
   ↓
prospective research
   ↓
clinical validation where applicable
```

Numerical performance on a retrospective dataset is not proof of clinical utility.

---

## Future development

The next priorities are:

1. strengthen end-to-end integration tests;
2. formalize schemas, identifiers, units and provenance contracts;
3. make experiment runs reproducible and versioned;
4. expand modality adapters for the datasets actually available in `data/raw/`;
5. improve uncertainty and calibration evaluation;
6. add predictive/mechanistic modelling only after reliable data and validation foundations are established;
7. continue development of the browser interface without coupling it to assumptions about unavailable data.

---

## Safety and limitations

`testHP` is a **research prototype**. It must not be used to diagnose disease, prescribe treatment, determine biological age for medical purposes, or make autonomous clinical decisions.

The project may eventually support research into healthy longevity and biological rejuvenation, but such goals are research hypotheses and ambitions, not demonstrated capabilities of the current software.

A complete predictive digital biological twin, clinically validated multimodal fusion, clinically validated ageing models and clinical decision support are **not currently implemented**.

---

## License / dataset licenses

Software licensing and dataset licensing are separate concerns. Individual public datasets may impose attribution, non-commercial, data-use or redistribution requirements. Before redistributing or publishing data from `data/raw/`, check the license and terms of the original dataset.
