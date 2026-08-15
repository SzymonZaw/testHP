# Human Pathology Platform

## Multimodal monitoring of biological state

This project aims to build a research platform capable of monitoring the state of a human organism — or a selected fragment of it — across multiple biological scales and over time.

The central idea is not to build a single classifier that answers only whether something is “healthy” or “diseased”. The system should progressively combine observations from different sources and resolutions, identify regions that deserve closer inspection, and allow analysis to move from the macroscopic level toward tissue, cellular, molecular and non-image evidence.

The long-term research goal is to investigate whether such a multimodal system can support the detection and monitoring of:

- disease-related abnormalities,
- biological ageing and age-associated changes,
- changes that precede an obvious clinical manifestation,
- spatially localized abnormalities,
- and changes in biological state over time.

The platform is intended as a **research system**, not as an autonomous diagnostic or clinical decision-making system.

---

## 1. The central research idea

The intended workflow is:

```text
Raw observations
      ↓
Data discovery and validation
      ↓
Modality-specific measurements
      ↓
Feature extraction
      ↓
Spatial and temporal organization
      ↓
Multimodal integration
      ↓
Detection of deviations / areas of interest
      ↓
Progressive deeper analysis
      ↓
Research evidence and biological interpretation
```

A key design principle is **progressive resolution**:

```text
Organism
   ↓
Body region / fragment
   ↓
Spatial zone
   ↓
Tissue
   ↓
Cell
   ↓
Cell properties / molecular state
```

The system should not be required to perform the deepest analysis everywhere. Broad observations should identify areas that deserve closer inspection, after which higher-resolution data can be analyzed for the selected region.

This leads to the long-term concept of a **digital biological twin**: a spatially and temporally organized computational representation to which observations from different modalities can be attached.

---

## 2. Digital twin and progressive “zoom”

The digital twin is intended to become the **spatial organization layer for multimodal evidence**, not merely a 3D visualization.

For an investigated organism fragment, the future system should be able to:

1. reconstruct a spatial representation,
2. divide it into meaningful zones,
3. attach measurements and observations to those zones,
4. compare the current state with previous observations,
5. identify zones requiring closer inspection,
6. let the researcher select a zone for deeper analysis,
7. connect macroscopic observations with tissue, cellular, molecular and other measurements when an explicit relationship exists.

Conceptually:

```text
                 ORGANISM / FRAGMENT
                         │
                   DIGITAL TWIN
                         │
                ┌────────┴────────┐
                │                 │
             spatial           temporal
              model             history
                │                 │
                └────────┬────────┘
                         │
                  multimodal data
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      macro            tissue          molecular
        │                │                │
      images            WSI             RNA
        │                │                │
        └────────────────┼────────────────┘
                         │
                     cellular
                       state
                         │
                  disease / ageing
```

The first practical fragment used to test this idea is the **hand**. It is sufficiently constrained to develop the architecture while still allowing future measurements at very different scales.

---

## 3. Disease and ageing are independent dimensions

Disease and ageing should not be collapsed into one universal “health score”.

The final system should conceptually maintain at least two independent dimensions:

### Disease-related state

Examples include validated evidence of:

- tissue damage,
- pathological morphology,
- abnormal cellular behaviour,
- tumour-related changes,
- inflammation,
- or other disease-associated patterns.

### Ageing-related state

Examples include validated evidence associated with:

- cellular senescence or other ageing-related cellular states,
- age-associated molecular programs,
- tissue-level ageing,
- structural degradation,
- or other ageing-associated patterns.

This creates a useful conceptual state space:

| Disease-related evidence | Ageing-related evidence | Conceptual state |
|---|---|---|
| Low | Low | No detected abnormality within the analyzed evidence |
| Low | High | Ageing-related change without detected disease-related abnormality |
| High | Low | Disease-related abnormality without strong ageing evidence |
| High | High | Disease-related and ageing-related evidence both present |

These are **future research categories**, not current diagnostic outputs.

At the cellular level, one long-term research question is:

> Is this cell showing evidence of pathological damage, ageing-related change, both, or neither?

The answer must be based on validated evidence appropriate to the available modality. “Cell age” must not be inferred from an image unless a validated method supports that inference.

---

## 4. Data architecture

The repository contains several modalities. They should not be understood as four isolated products. They represent different levels of observation that may eventually contribute to the same biological-state model.

### `data/raw/hand/` — multimodal fragment entry point

`hand/` is the first practical user-data entry point and should be understood as a **future multimodal observation space**, not as a permanently fixed “hand image” dataset.

It currently contains:

- `InterHand2_6M/` — external reference data for hand pose / hand understanding,
- `media/` — simple video/media test data,
- `own_cohort/` — the intended location for the researcher’s own hand images and future personal observations.

The current files are deliberately simple and mainly test whether the platform can discover, validate and process inputs.

In the future, `hand/` may contain:

- high-quality RGB images,
- depth information,
- video and temporal observations,
- 3D observations,
- microscopy or other tissue-level images,
- cellular images,
- whole-slide or larger-scale tissue data,
- numerical measurements,
- molecular measurements,
- laboratory-style values,
- structured metadata,
- and textual or other non-image evidence.

Therefore the conceptual definition is:

> **`hand/` contains multimodal observations associated with an investigated hand or other selected organism fragment, including data that may extend far beyond ordinary photographs and video.**

`InterHand2_6M` is external reference/test material, not the researcher’s own cohort.

### `data/raw/images/` — macroscopic skin

`images/` contains skin imagery primarily obtained using ordinary cameras rather than microscopy.

The current conceptual groups are:

- `aging_skin/` — visible changes associated with ageing,
- `lesions/` — skin abnormalities or lesions not primarily defined as ageing,
- `normal_skin/` — ordinary healthy/reference skin,
- `pathology/` — a historical category whose exact intended scientific scope still needs to be confirmed.

This layer represents **macroscopic skin observation**.

Potential future analyses may include validated measurements of colour, texture, geometry, visible surface characteristics, lesion morphology, spatial distribution and temporal change.

Descriptive image measurements must remain distinct from biological conclusions.

### `data/raw/wsi/` — tissue / histology

`wsi/` represents the **tissue-level** view.

Whole Slide Images and related pathology data may eventually support analysis of:

- tissue architecture,
- cellular organization,
- cell density,
- morphology,
- spatial relationships,
- pathological structures,
- and other histological features.

This level allows the system to move beyond “what does the surface look like?” toward “what is happening inside the tissue?”.

Metadata-only files or missing/unsupported slides must not be presented as successful tissue analysis.

### `data/raw/rna/` — molecular / transcriptomic level

`rna/` represents the **molecular level**.

Depending on the actual datasets, future analyses may include:

- gene expression measurements,
- differential expression,
- molecular signatures,
- pathway activity,
- ageing-associated programs,
- disease-associated programs,
- and other validated transcriptomic characteristics.

RNA and WSI therefore answer different questions:

> **RNA:** what is happening at the molecular level?

> **WSI:** what is happening in the tissue and its spatial organization?

Their integration may become scientifically important — for example, investigating whether a molecular program is associated with a particular tissue phenotype. Such integration requires an explicit relationship between observations, such as a shared subject, sample, specimen or other validated identifier. It must never be inferred from filenames or dataset names alone.

---

## 5. Evidence hierarchy

The platform follows an **evidence-first** principle.

A result should only be reported when the required evidence exists and the corresponding analysis was actually executed.

For example:

```text
RGB image available
    → image measurements possible
    → tissue biology not automatically established

WSI available
    → tissue-level analysis possible
    → molecular state not automatically established

RNA available
    → molecular analysis possible
    → spatial tissue relationship not automatically established

Explicit cross-modal identifier available
    → multimodal relationship may be analyzed
```

The platform must never turn filenames, dataset names, placeholders, missing files, metadata-only input or unsupported assumptions into biological findings.

Current descriptive measurements such as image dimensions, RGB statistics, row counts or structured-node counts are **measurements of available input**, not diagnoses or biological conclusions.

---

## 6. Development roadmap

The project should be developed in the following order. The sequence is intentional: scientific definition comes before large-scale implementation.

### Phase 1 — Scientific definition and data audit

**Goal:** understand what each real dataset can actually contribute.

For every dataset we will document:

1. what files exist,
2. what the files actually contain,
3. what metadata exists,
4. what is missing or malformed,
5. what can be measured,
6. what biological questions can reasonably be asked,
7. what output would constitute a useful research result,
8. what cannot be concluded.

The first target is:

```text
raw/hand/
├── InterHand2_6M/
├── media/
└── own_cohort/
```

Then we will inspect `images/`, `wsi/` and `rna/` systematically.

### Phase 2 — Data-to-result specifications

For every dataset create a research specification:

```text
Dataset
  ↓
Available evidence
  ↓
Measurable variables
  ↓
Derived features
  ↓
Biological question
  ↓
Potential research result
  ↓
Validation method
  ↓
Possible multimodal connections
```

This becomes the scientific specification for implementation.

### Phase 3 — Stable data contracts

Formalize:

- subject identifiers,
- sample/specimen identifiers,
- anatomical locations,
- spatial coordinates,
- timestamps and visits,
- units,
- acquisition metadata,
- dataset versions,
- model/analysis versions,
- provenance,
- uncertainty and quality flags.

This phase is essential before cross-modal integration.

### Phase 4 — Modality-specific analysis pipelines

Implement validated routines independently for:

- hand / macroscopic observations,
- skin images,
- WSI / histology,
- RNA / transcriptomics,
- future cellular data,
- future non-image measurements.

Each analysis should have an explicit input contract, output contract, validation strategy and evidence boundary.

### Phase 5 — Real user-data workflow for `hand/own_cohort/`

Transform the current simple test directory into a structured representation of repeated observations of a real subject or cohort.

The future structure should support multiple visits, acquisition methods, resolutions, spatial zones, temporal comparison and links to deeper data.

### Phase 6 — Digital twin foundation

Create a spatial representation of the investigated fragment and a stable coordinate/zone system.

The twin should store observations and state history rather than simply render geometry.

### Phase 7 — Progressive macro-to-micro analysis

Implement the ability to move from:

```text
macroscopic observation
        ↓
region of interest
        ↓
tissue
        ↓
cell
        ↓
molecular / numerical state
```

Broad analysis should help prioritize where deeper analysis is useful.

### Phase 8 — Cellular state analysis

Once appropriate cellular data exist, develop validated methods for cellular morphology and state.

The long-term objective is to characterize separate dimensions such as:

- normal/reference state,
- disease-related abnormality,
- ageing-related state,
- molecular state,
- spatial context,
- uncertainty.

This phase must explicitly avoid claiming “cell age” or “cancer” without validated evidence.

### Phase 9 — Longitudinal monitoring

Introduce repeated observations of the same subject/fragment.

The system should eventually distinguish, where validated measurements support it:

- stable state,
- improvement,
- deterioration,
- newly emerging abnormality,
- change requiring deeper investigation.

A single run characterizes a state; monitoring requires time and repeated observations.

### Phase 10 — Multimodal integration

Only after the individual modalities are reliable should they be combined.

Potential integrations include:

- macroscopic image ↔ WSI,
- WSI ↔ RNA,
- macroscopic region ↔ tissue region,
- cellular morphology ↔ molecular state,
- spatial state ↔ temporal change.

Every connection must have explicit provenance and an evidence path.

### Phase 11 — Unified biological-state model

Develop a unified representation that separates at least:

- disease-related evidence,
- ageing-related evidence,
- normal/reference evidence,
- uncertainty,
- missing evidence,
- and evidence requiring deeper analysis.

The goal is not to hide uncertainty behind a single “health score”.

### Phase 12 — Validation and benchmarking

Evaluate analyses against appropriate reference data and known measurements/labels where available.

Validation should cover:

- accuracy,
- sensitivity/specificity where appropriate,
- robustness,
- reproducibility,
- calibration and uncertainty,
- cross-dataset generalization,
- subgroup performance,
- and failure modes.

A retrospective metric is not proof of clinical utility.

### Phase 13 — Provenance, reproducibility and audit

Every research result should be traceable through:

```text
Run
 ↓
Dataset
 ↓
File / sample
 ↓
Analysis version
 ↓
Measured variables
 ↓
Derived result
 ↓
Interpretation
```

Large raw datasets should remain outside source control when appropriate, while the run record preserves the evidence trail needed to audit and reproduce a result.

### Phase 14 — Research interface

The final interface should allow a researcher to:

1. provide new data,
2. see what was recognized,
3. see which analyses were possible,
4. inspect detected regions of interest,
5. move to deeper resolution,
6. compare observations over time,
7. inspect evidence behind every result,
8. and export the research record.

### Phase 15 — Scientific and prospective validation

Only after the analytical system is reliable should the project progress toward:

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
clinical validation, where applicable
   ↓
regulatory / safety assessment, where applicable
```

---

## 7. Current implementation status

The current repository is a **research prototype / foundation**, not the final biological monitoring system.

The existing platform already provides an evidence-oriented pipeline and research dashboard with:

- raw dataset discovery,
- validation and coverage reporting,
- descriptive measurements for supported local files,
- pipeline stage reporting,
- run identifiers and timestamps,
- provenance information,
- real-data visualizations,
- JSON/CSV export,
- explicit limitations,
- and protection against unsupported biological inference.

The current descriptive analyses deliberately remain below the level of biological interpretation. This is intentional. The immediate next task is to determine scientifically meaningful outputs for the real datasets before implementing modality-specific biological analyses.

The repository also contains earlier architectural foundations for observations, quality/uncertainty, multimodal fusion, hierarchical state, digital-twin snapshots, longitudinal analysis, anomaly/change detection, measurement planning, intervention surveillance, validation and audit. These components should be integrated with the real-data workflow only after their contracts are checked against the actual datasets.

---

## 8. Immediate working plan

The next work should **not** be driven by adding arbitrary features to the dashboard.

We will inspect the actual data in a fixed order and decide what each dataset should contribute to the final system.

### First: `raw/hand/`

For `InterHand2_6M`, `media` and `own_cohort` we will establish:

- what the data are,
- what they are useful for,
- what can be measured now,
- what richer future data should look like,
- what the desired research output should be,
- how the data can contribute to the digital twin,
- and how they can connect to deeper tissue/cellular/molecular observations.

### Then: `raw/images/`

We will define what should be extracted from:

- normal skin,
- ageing-related skin changes,
- non-ageing lesions,
- and the currently ambiguous `pathology` category.

### Then: `raw/wsi/`

We will determine which tissue-level measurements are scientifically useful and which WSI datasets can realistically support them.

### Then: `raw/rna/`

We will determine which molecular variables and biological programs can be extracted and which datasets can eventually be connected to tissue-level observations.

### Finally: cross-modal design

Only after the individual datasets have been understood will we decide which cross-modal relationships are scientifically justified.

---

## 9. Non-negotiable design principles

### Evidence before interpretation

The system must distinguish what was measured from what was inferred.

### No invented links

A relationship between datasets, subjects, samples, regions or cells must be supported by an explicit identifier or a validated spatial/experimental relationship.

### Disease and ageing are separate dimensions

A biological system may show ageing-related change without disease, disease without strong ageing evidence, both, or neither.

### Resolution must be explicit

Every result should indicate the level at which it was obtained: macroscopic, tissue, cellular, molecular or non-image.

### Missing data must remain visible

Unavailable input is a research limitation, not a negative biological finding.

### Uncertainty must remain visible

The system should report uncertainty and evidence boundaries instead of converting incomplete evidence into false certainty.

### Monitoring requires time

A monitoring system needs repeated observations and longitudinal comparison. A single run can characterize a state, but cannot by itself establish a trajectory.

### Research first

The platform is being developed as a research system. It must not be presented as an autonomous clinical diagnostic or treatment decision system without appropriate scientific, clinical and regulatory validation.

---

## 10. Long-term vision

The long-term vision is a system in which a researcher can provide new observations of a selected part of an organism and receive a transparent representation of its current state:

```text
New observation
      ↓
Identify and register the observed fragment
      ↓
Update digital twin
      ↓
Compare with previous state
      ↓
Analyze available modalities
      ↓
Identify unusual / changing regions
      ↓
Prioritize deeper analysis
      ↓
Tissue → cell → molecular evidence
      ↓
Disease / ageing / normal-state evidence
      ↓
Research report with provenance and uncertainty
```

The ultimate objective is therefore not simply **image classification**, **RNA analysis** or **pathology analysis** in isolation.

It is the development of a **transparent multimodal framework for understanding and monitoring biological state across scales and over time**.

The system should be able to say not only:

> “something looks different,”

but eventually, when sufficient validated evidence exists:

> **where the change is, at what biological level it is observed, whether it is more consistent with disease-related or ageing-related change, what additional evidence is needed, how the observation changed over time, and exactly which measurements support that conclusion.**

That final capability is the long-term research target.
