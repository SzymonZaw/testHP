# Stages 21–25 — personal hand implementation

This pass turns the scientific contracts from stages 1–10 and the core models from the foundation work into one reproducible personal-hand run.

## Stage 21 — Connect `own_cohort` to the core observation layer

Implemented in `backend/hand_pipeline.py`.

The existing `backend.hand_vision.analyze_own_cohort()` output is converted into the core `Measurement` model.

Each measurement keeps:

- explicit `subject_id`;
- explicit `timepoint_id`;
- modality = `hand`;
- source file;
- anatomical zone;
- biomarker/metric name;
- value and unit;
- processing version;
- uncertainty metadata.

The important boundary is preserved: these are **observations**, not diagnoses.

## Stage 22 — Quality and uncertainty

Every generated measurement receives a transparent quality score and flags based on:

- brightness plausibility;
- image contrast;
- expected hand count;
- handedness confidence when available.

The existing `MeasurementQualityEngine` is then used to determine whether each measurement is usable.

Quality never changes the measured value and does not convert a low-quality measurement into a biological conclusion.

## Stage 23 — Stable spatial zones + Digital Biological Twin

The pipeline creates stable hand zones:

```text
hand
├── wrist
├── palm
├── thumb
├── index
├── middle
├── ring
└── little
```

The zones are represented as anatomical `site` locations under `hand`.

A `DigitalBiologicalTwin` snapshot is then created for the explicit subject and timepoint. The snapshot contains measurements, quality, zone mapping, provenance and the explicit interpretation boundary.

The twin is currently an **evidence container**, not a physiological simulator.

## Stage 24 — Longitudinal comparison

The pipeline can compare two explicit timepoints for the same subject.

It matches observations by:

- anatomical zone;
- metric;
- explicit subject/timepoint context.

It reports:

- baseline value;
- current value;
- absolute change;
- relative change.

The result is labelled `observed_change`.

No threshold is interpreted as disease, ageing or deterioration. A future clinical/scientific interpretation layer must define and validate such thresholds separately.

Without a baseline, this stage is explicitly marked inactive rather than fabricating a trend.

## Stage 25 — Reproducible research-run contract

The CLI `scripts/run_hand_pipeline.py` executes stages 21–25 and writes a machine-readable run record.

Example:

```powershell
python -m scripts.run_hand_pipeline --root data/raw/hand/own_cohort --subject own_cohort --session session-001 --timepoint T0
```

The output contains:

- input analysis;
- core measurements;
- quality assessments;
- stable zone map;
- digital-twin snapshot;
- longitudinal changes when a baseline is supplied by the Python API;
- explicit availability boundary for disease, ageing and cellular-age results.

## Important MediaPipe compatibility fix

The installed MediaPipe version may expose the Tasks API without exposing `mp.solutions` at the top level. `backend.hand_vision` now attempts both:

1. the legacy `mediapipe.solutions.hands` path;
2. the compatibility `mediapipe.python.solutions.hands` path.

If neither exists, the error now explains that a Tasks `HandLandmarker` adapter and `.task` model asset are required instead of falsely saying that the package is simply not installed.

## What is now real

The personal hand pipeline now has this executable chain:

```text
raw/hand/own_cohort
        ↓
file/image analysis
        ↓
hand detection + landmarks
        ↓
core Measurements
        ↓
quality + uncertainty
        ↓
stable anatomical zones
        ↓
Digital Biological Twin snapshot
        ↓
longitudinal observed change
        ↓
research-run JSON
```

## What is still deliberately unavailable

The following are **not** claimed by stages 21–25:

- cancer detection;
- disease diagnosis;
- cellular damage detection;
- cellular age estimation;
- senescence classification;
- biological age estimation;
- tissue pathology from ordinary RGB hand photographs.

Those require modality-specific validated evidence and models. The architecture is now ready to attach such evidence progressively at the appropriate biological level.
