# Hand modality — research specification

## Status

This document completes the scientific-definition phase for `data/raw/hand/`. It defines what the current hand sources are for, what the system should measure, what it may interpret later, and what the final `hand` result should look like.

It is a **specification**, not a claim that all listed analyses are already implemented.

## 1. Target answer

For a future personal hand run, the system should answer progressively:

1. **What did I actually receive?**
2. **Is the input usable and of sufficient quality?**
3. **What can be measured at macroscopic level?**
4. **Where are the hand's anatomical regions and which regions differ from the person's reference/baseline?**
5. **Which region deserves closer inspection?**
6. **What additional measurement would reduce the uncertainty?**
7. If deeper data exist for that region: **what is observed at tissue/cellular/molecular level?**
8. Only after validated modality-specific analysis: **is the evidence more consistent with normal variation, ageing-related change, disease-related abnormality, both, or insufficient evidence?**

The system must be allowed to answer **insufficient evidence** at every level.

## 2. Role of the current sources

| Source | Role | Should become personal evidence? | Main use now |
|---|---|---:|---|
| `own_cohort/` | user's own hand photographs | Yes, when explicitly registered to a subject/timepoint | build personal image pipeline |
| `media/` | user's future videos/media | Yes, when explicitly registered | future temporal/motion pipeline; current files are empty placeholders |
| `InterHand2_6M/` | external reference dataset | No | develop/test hand pose, landmarks, 3D and spatial reconstruction |

`hand/` is intentionally broader than RGB photographs. Future hand-associated observations may include RGB/depth images, video, 3D data, microscopy, cellular measurements, numerical values and other non-image evidence.

## 3. Information map

### Level A — acquisition/input

Directly measurable from almost every future source:

- file existence,
- format,
- byte size,
- readability,
- image dimensions,
- frame count/duration for video,
- acquisition timestamp when present,
- device/acquisition metadata when present,
- explicit subject/session/sample identifiers.

**Output:** input quality and provenance.

### Level B — macroscopic hand

From good RGB/depth photographs or video:

- hand presence and localization,
- segmentation mask,
- orientation,
- visible hand contour,
- anatomical landmarks,
- finger/joint geometry,
- hand proportions,
- approximate 2D/3D geometry where depth is available,
- surface colour/texture measurements,
- image-quality indicators.

**Output:** measurable macroscopic state of the hand.

### Level C — spatial regions

Create a stable region system, for example:

- wrist,
- palm,
- thumb,
- index,
- middle,
- ring,
- little finger,
- individual joints,
- configurable surface regions.

Every region should have a stable identifier in the digital twin so that later observations can be attached to it.

**Output:** region-level measurements and candidate areas of interest.

### Level D — tissue

Future microscopy/WSI/deeper hand data may provide:

- tissue architecture,
- cell density,
- morphology,
- spatial organization,
- pathological structures,
- tissue-level ageing features.

**Output:** tissue-level evidence linked to a specific region only when the spatial/sample relationship is explicit.

### Level E — cell

Future cellular data may provide:

- cell segmentation,
- morphology,
- size/shape,
- nuclear/cytoplasmic features,
- cellular damage markers,
- proliferation or other validated state markers,
- senescence/ageing-associated markers where an appropriate assay exists.

**Output:** cellular state dimensions. “Cell age” is not a generic image property and must not be reported without a validated biological measurement/model.

### Level F — molecular / non-image

Future hand-associated measurements may include:

- gene expression,
- molecular signatures,
- biochemical values,
- laboratory measurements,
- structured sensor values,
- textual/metadata evidence.

**Output:** molecular or non-image state dimensions, with units and provenance.

## 4. Observation versus interpretation

### Observation

An observation is something the system can point to and reproduce from the input or a validated measurement routine.

Examples:

- `hand_width = 84.2 mm` from a calibrated/depth-supported acquisition;
- `index_MCP_angle = 17.4°`;
- `region R17 mean brightness = 0.72/1`;
- `video duration = 18.4 s`;
- `region R17 contains a 14% texture deviation from the personal baseline`.

### Interpretation

Interpretation is a higher-level statement requiring a validated model or biological reference.

Examples:

- possible abnormality,
- possible ageing-related change,
- pathology-compatible morphology,
- cellular senescence-compatible state,
- disease-related signal.

Interpretation must always reference the evidence and analysis version that produced it.

## 5. Analysis ladder

The hand pipeline should implement a progressive ladder rather than one giant classifier:

```text
H0  Input audit
    ↓
H1  Image/video quality
    ↓
H2  Hand detection + segmentation
    ↓
H3  Landmarks + geometry + orientation
    ↓
H4  Anatomical zoning / digital-twin registration
    ↓
H5  Personal baseline comparison
    ↓
H6  Region-of-interest prioritization
    ↓
H7  Higher-resolution tissue analysis
    ↓
H8  Cellular analysis
    ↓
H9  Molecular/non-image analysis
    ↓
H10 Multimodal interpretation
    ↓
H11 Longitudinal monitoring
```

Not every run executes every level. A run should stop at the deepest level supported by the available evidence and clearly state why deeper levels were not executed.

## 6. Proposed `hand` result contract

The final hand result should contain these sections:

```text
HAND RUN
├── subject / session / timepoint
├── acquisition quality
├── macroscopic measurements
├── anatomical regions
├── baseline comparison
├── regions of interest
├── deeper evidence available?
│   ├── tissue
│   ├── cell
│   └── molecular/non-image
├── interpretation
│   ├── normal/reference evidence
│   ├── disease-related evidence
│   ├── ageing-related evidence
│   └── insufficient evidence
├── uncertainty
├── recommended next measurement
└── provenance
```

The key result is therefore not a single health score. It is a **spatially organized evidence map** with explicit uncertainty and a path toward deeper analysis.

## 7. What the current data can support

### `own_cohort/`

Current photographs are suitable for the first implementation of:

- file/input validation,
- image dimensions,
- raster statistics,
- hand detection/segmentation,
- landmark detection,
- orientation,
- geometric measurements,
- region generation.

They are **not sufficient by themselves** to claim:

- cancer,
- cellular damage,
- cellular age,
- senescence,
- tissue pathology,
- or a biological-age value.

### `media/`

The current MP4 placeholders contain no usable video data. The future adapter should support:

- temporal hand tracking,
- pose trajectories,
- range of motion,
- velocity,
- stability,
- symmetry,
- repeatability.

### `InterHand2_6M/`

Use as an external development/reference source for:

- 2D/3D landmarks,
- hand pose,
- camera-aware reconstruction,
- anatomical geometry,
- annotation handling,
- region registration.

It should not be mixed with personal observations as if it were another timepoint of the same subject.

## 8. Definition of “area requiring closer inspection”

A region should become an ROI only when at least one transparent criterion is met, such as:

- statistically unusual relative to the person's validated baseline,
- persistent change across repeated observations,
- low measurement quality/uncertainty requiring better acquisition,
- disagreement between modalities,
- or a validated modality-specific detector identifies a candidate pattern.

A region should **not** become an ROI merely because it looks different from another person's hand or because a public dataset contains a similar image.

## 9. Longitudinal contract

A longitudinal claim requires at minimum:

- explicit subject identifier,
- explicit anatomical region or spatial registration,
- at least two independent timepoints,
- comparable acquisition/measurement definitions,
- provenance for both observations.

The current single-run dashboard must therefore continue to report “trajectory not established”.

## 10. Implementation order for `hand`

1. **H1 input-quality adapter** — finish reliable image/video inventory and provenance.
2. **H2 hand detector/segmenter** — locate the hand in `own_cohort` images.
3. **H3 landmarks and geometry** — use `InterHand2_6M` as a reference/benchmark and then apply to own images.
4. **H4 digital-twin hand v0** — stable wrist/palm/finger/joint/ROI coordinate system.
5. **H5 baseline store** — record repeated observations for the same subject and region.
6. **H6 ROI prioritization** — produce transparent “inspect next” regions, not diagnoses.
7. **H7 deep-data linking** — define how a future tissue/cellular/molecular sample attaches to a hand region/timepoint.
8. **H8+ biological interpretation** — only after the appropriate deep data and validation exist.

## 11. Definition of success for the hand phase

The hand phase is complete enough to move to `images/` when the system can:

- accept a new personal hand image,
- validate and record its provenance,
- locate the hand,
- generate stable anatomical regions,
- calculate reproducible macroscopic measurements,
- compare the same region across at least two timepoints,
- identify a transparent ROI for deeper inspection,
- represent the ROI in the digital twin,
- and explicitly say when deeper biological evidence is missing.

At that point `images/`, `wsi/` and `rna/` can be specified using the same scientific framework without prematurely fusing their outputs.
