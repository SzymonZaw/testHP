# Stages 26–34 — from hand state to multimodal evidence

This pass implements the next layer after stages 1–25. The goal is to make the project progress from a personal hand observation stream toward a multiscale evidence architecture without pretending that technical measurements are diagnoses.

## Stage 26 — Formal `Hand State`

The hand is represented as multiple independent state dimensions:

- `macroscopic`: geometry, landmarks, surface descriptors;
- `functional`: movement and temporal features;
- `surface`: visible skin observations;
- `tissue`: microscopic/WSI evidence;
- `cellular`: cell and nuclear measurements;
- `molecular`: RNA and other non-image measurements;
- `disease_related`: unavailable until a validated interpretation method exists;
- `ageing_related`: unavailable until a validated ageing endpoint exists;
- `longitudinal`: explicit change between comparable timepoints;
- `uncertainty`: measurement quality and confidence;
- `missing_evidence`: what the current run cannot observe.

The state is deliberately not collapsed into one health score.

## Stage 27 — `Hand Observation Ontology`

Every evidence record has a stable vocabulary:

```text
subject_id
source_id
modality
biological_level
region_id
result_type
metric
value
unit
status
uncertainty
provenance
```

`result_type` distinguishes direct `observation`, `derived_feature`, `quality` and later `interpretation`.

`status` distinguishes `available`, `partial`, `unavailable` and `not_applicable`.

This makes data from hand, images, WSI and RNA representable in the same evidence layer without making them biologically equivalent.

## Stage 28 — First real Digital Biological Twin contract

The twin is a structured state container, not a visual 3D model.

```text
subject
└── hand
    ├── wrist
    ├── palm
    ├── thumb
    ├── index
    ├── middle
    ├── ring
    └── little

history: T0 → T1 → T2 ...
evidence: observations linked to timepoint/region
```

Each snapshot stores evidence references and can later receive deeper tissue, cellular and molecular observations.

The twin does not automatically connect public datasets to the personal subject.

## Stage 29 — T0 → T1

The existing hand pipeline now supplies explicit longitudinal comparison. A second timepoint is matched only by the same subject, anatomical zone and metric. The result is labelled `observed_change`.

A change is not automatically deterioration, disease or ageing.

The multiscale runner therefore treats longitudinal interpretation as a separate validated layer.

## Stage 30 — `media/`: temporal hand evidence

The new media adapter scans `data/raw/hand/media/` and, for readable video, measures:

- FPS;
- frame count;
- duration;
- sampled frame count;
- mean frame-to-frame change.

These are temporal observations. They are not converted into a functional diagnosis.

Empty placeholder video files remain unavailable evidence.

## Stage 31 — `images/`: macroscopic skin

The image adapter scans the existing skin-image tree and computes descriptive measurements from readable images:

- dimensions;
- pixel count;
- mean brightness;
- mean RGB channels;
- average channel dynamic range.

The result is a macroscopic/surface observation. The adapter does not infer cancer, disease or cellular age.

## Stage 32 — `wsi/`: macro → tissue → microscopic → cellular

The WSI adapter begins with the technical layer and records DICOM observations such as:

- readability;
- matrix rows/columns;
- DICOM identifiers when present.

The architecture explicitly reserves the next ladder:

```text
macro region
    ↓
 tissue region
    ↓
 microscopic region / tile
    ↓
 cell / nucleus
    ↓
 validated cellular interpretation
```

The current repository's small DICOM samples are therefore used for metadata validation, not presented as a complete WSI pathology benchmark.

## Stage 33 — `rna/`: molecular layer

The RNA adapter audits local tabular/textual evidence and records:

- rows inspected;
- finite numeric values;
- numeric minimum/maximum where available;
- parse errors as quality records.

It does not infer a pathway, disease or biological age merely from numeric ranges.

## Stage 34 — explicit multimodal fusion

Fusion is now implemented as a provenance-safe join.

A record can enter a linked group only when an explicit `subject_id` exists. Region-level linkage additionally requires an explicit `region_id`.

```text
HAND
  +
IMAGES
  +
WSI
  +
RNA
  ↓
explicit evidence groups
  ↓
Digital Biological Twin
  ↓
longitudinal state
  ↓
validated interpretation (future)
```

Records without explicit subject linkage are retained as evidence but rejected from personal multimodal fusion. This is intentional.

## CLI

From the repository root:

```powershell
python -m scripts.run_multiscale_pipeline --root data/raw --subject own_cohort --timepoint T0
```

Output defaults to `data/longitudinal/multiscale_run.json`.

## What is now implemented

- a common evidence record for multiple modalities;
- a structured digital-twin state container;
- temporal video descriptors;
- macroscopic skin descriptors;
- DICOM/WSI technical observations;
- RNA/tabular audit observations;
- explicit-link multimodal fusion;
- a reproducible CLI run contract.

## What remains intentionally unavailable

The pipeline still does **not** claim:

- cancer detection;
- disease diagnosis;
- cellular damage from ordinary photographs;
- cellular age;
- senescence;
- biological age;
- pathological meaning of a folder name;
- a personal link to public datasets without explicit identifiers.

The next scientific work should validate each deeper modality-specific interpretation before it is allowed into the final health/state layer.
