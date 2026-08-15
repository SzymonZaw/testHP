# Hand scientific foundation — stages 1–5

## Purpose

This document freezes the scientific definition of the `hand` modality before deeper implementation. It applies to `data/raw/hand/` and is designed around the long-term project goal: monitor the state of an organism or selected fragment across biological scales, over time, while keeping measurements, interpretation and uncertainty separate.

The hand is the first practical test object for this architecture. It is not restricted to photographs. Future hand-associated evidence may include RGB images, depth/RGB-D, video, 3D observations, tissue/WSI or microscopy, cellular measurements, RNA and other numerical/textual measurements.

---

## Stage 1 — Define the target system response

### What the future system should answer

For a personal hand run, the system should progressively answer:

1. **What data entered the run?**
2. **Is the data usable and of sufficient quality?**
3. **What can be directly measured at macroscopic level?**
4. **Where are the anatomical regions of interest?**
5. **Which regions deserve closer inspection?**
6. **What additional evidence would reduce uncertainty?**
7. If deeper data exist for a selected region, **what is observed at tissue, cellular or molecular level?**
8. Only after a validated modality-specific analysis, **what biological interpretation is supported?**

The system must be allowed to answer **insufficient evidence** at every level.

### Final hand result

The result is **not a single unexplained health score**. The intended output is a spatially organized evidence map:

```text
HAND RUN
├── input / acquisition quality
├── macroscopic measurements
├── anatomical regions
├── personal/reference comparison
├── regions requiring closer inspection
├── deeper evidence available?
│   ├── tissue
│   ├── cell
│   └── molecular / non-image
├── disease-related evidence
├── ageing-related evidence
├── normal/reference evidence
├── uncertainty
├── missing evidence
└── provenance
```

### What “state” means in this project

The project is intended to monitor multiple dimensions rather than collapse everything into one number. At minimum, the long-term hand state should preserve:

- structural/macroscopic state,
- functional/motion state,
- surface/skin state,
- tissue state,
- cellular state,
- molecular state,
- disease-related evidence,
- ageing-related evidence,
- longitudinal change,
- uncertainty and missing evidence.

Disease and ageing are **independent dimensions**. A region may show ageing-associated evidence without disease-associated evidence, disease-associated evidence without strong ageing evidence, both, neither, or insufficient evidence.

---

## Stage 2 — Audit `raw/hand/`

### Current sources

| Source | Scientific role | Personal evidence? | Current use |
|---|---|---:|---|
| `own_cohort/` | User's own hand observations | **Yes** | First personal-input pipeline |
| `media/` | User's future video/media observations | **Yes, when explicitly registered** | Future temporal/functional pipeline |
| `InterHand2_6M/` | External reference/benchmark dataset | **No** | Hand pose, landmark and 3D algorithm development/validation |

### `own_cohort/`

Current files are simple hand photographs. They are the intended path for testing the personal-data workflow.

They can support, once the acquisition is valid:

- image quality,
- hand detection,
- hand count,
- handedness where reliable,
- landmarks,
- 2D geometry,
- normalized proportions,
- anatomical zoning,
- spatial ROI generation.

They do **not** by themselves support claims about:

- cancer,
- cellular damage,
- cellular age,
- senescence,
- tissue pathology,
- biological age,
- or disease state.

### `media/`

This directory is the future input location for personal videos. Empty placeholder files are **unavailable evidence**, not negative evidence.

Future video analysis should focus first on measurable temporal properties:

- hand detection/tracking,
- pose trajectory,
- movement range,
- movement speed,
- stability,
- symmetry,
- repeatability,
- surface changes over time.

Depth or other sensor channels should be represented as separate modality-specific evidence rather than hidden inside a generic video score.

### `InterHand2_6M/`

This is external reference data. Its value is methodological:

- annotated hand landmarks,
- 3D joint information,
- camera/capture context,
- pose variation,
- richer hand geometry,
- annotation formats useful for adapter development.

It must never be treated as another timepoint of the user's hand and must never establish a personal subject link.

### Audit rules

For every future hand input, the system should record:

- source role: `personal`, `benchmark`, or `placeholder`,
- modality,
- path/file identifier,
- format,
- byte size,
- readability,
- dimensions/frame count where applicable,
- acquisition timestamp if available,
- subject/session/timepoint if explicitly supplied,
- anatomical region if explicitly supplied,
- annotation availability,
- provenance,
- analysis version.

The audit layer must distinguish:

```text
missing input
≠ empty input
≠ unreadable input
≠ unsupported format
≠ usable input
```

---

## Stage 3 — Establish the role of each source

### `own_cohort` — personal observation stream

This is the most important source for the eventual user workflow.

Its role is to answer:

> “What can the system observe about this specific hand at this timepoint?”

It should become longitudinal after explicit registration of the subject, session and timepoint.

### `media` — dynamic/functional stream

Its role is:

> “What can the system observe about how this hand behaves over time?”

It is complementary to still images. A photograph captures a state; video can capture movement and temporal dynamics.

### `InterHand2_6M` — methodological reference

Its role is:

> “Can the hand-understanding algorithms reconstruct pose, landmarks and spatial geometry correctly on known reference data?”

It is not a health-data source for the user's digital twin.

### Future deeper hand data

The `hand/` architecture must remain open to additional evidence associated with a hand region:

```text
RGB / video / depth
        ↓
macroscopic hand
        ↓
anatomical zone
        ↓
selected ROI
        ↓
tissue / microscopy / WSI
        ↓
cellular measurements
        ↓
RNA / molecular / numerical evidence
```

The fact that this chain is possible does not mean the system may infer the deeper state from the shallower state. Each transition requires its own evidence.

---

## Stage 4 — Build the hand information map

The information map is the bridge between raw files and future scientific outputs.

### Level A — acquisition

**Inputs:** files, image streams, video, depth, metadata.

**Information:**

- existence,
- integrity,
- format,
- dimensions,
- frame count/duration,
- timestamps,
- acquisition device/settings,
- missing/empty/unsupported content.

**Output type:** direct observation / quality.

### Level B — macroscopic hand

**Inputs:** ordinary high-quality RGB/depth images or video.

**Information:**

- hand presence,
- hand localization,
- segmentation when validated,
- handedness,
- landmarks,
- orientation,
- hand contour,
- finger/joint geometry,
- proportions,
- surface colour/texture descriptors,
- depth-derived geometry where calibrated.

**Output type:** direct measurement / derived feature.

### Level C — anatomical regions

The hand should be divided into stable spatial regions. The initial computational zoning can use:

- wrist,
- palm,
- thumb,
- index,
- middle,
- ring,
- little finger.

The later scientific zoning can be refined to include:

- dorsal/palmar surface,
- thenar/hypothenar regions,
- individual joints,
- nails,
- configurable surface patches.

Each region must have a stable identifier in the digital twin.

**Output type:** spatial observation / ROI.

### Level D — tissue

**Inputs:** WSI, microscopy or other high-resolution tissue evidence linked to a region/sample.

**Information:**

- tissue architecture,
- compartment distribution,
- cellular density,
- morphology,
- spatial organization,
- tissue-level abnormalities,
- validated ageing-associated tissue features.

**Output type:** tissue measurement / validated interpretation.

### Level E — cellular

**Inputs:** microscopy/cell-resolution data or other validated cellular measurements.

**Information:**

- cell segmentation,
- size/shape,
- nuclear/cytoplasmic characteristics,
- cell density,
- spatial relationships,
- damage markers,
- proliferation markers,
- senescence/ageing-associated markers where an appropriate assay exists.

**Output type:** cellular observation / validated interpretation.

### Level F — molecular/non-image

**Inputs:** RNA, biochemical values, laboratory measurements, sensor values or structured textual/numerical evidence.

**Information:**

- expression values,
- molecular signatures,
- pathway activity,
- biomarkers,
- quantitative laboratory measurements,
- other non-image state variables.

**Output type:** measurement / derived molecular feature / validated interpretation.

### Level G — longitudinal

Repeated measurements add another dimension:

```text
T0 → T1 → T2 → T3 → …
```

Longitudinal information includes:

- baseline,
- absolute change,
- relative change,
- rate of change,
- persistence of change,
- change point,
- stability/repeatability.

A longitudinal claim requires explicit subject identity, comparable acquisition definitions and at least two relevant timepoints.

---

## Stage 5 — Define the biological level of each information type

Every result must declare the level at which it was obtained.

| Biological/technical level | Examples | Can be measured from current own-cohort RGB? |
|---|---|---:|
| Acquisition | file quality, dimensions, readability | **Yes** |
| Macroscopic | hand pose, landmarks, contour, proportions | **Yes, if detection succeeds** |
| Functional | motion, range of motion, stability | **No — real video needed** |
| Surface/skin | colour, texture, visible surface differences | **Partly** |
| Anatomical region | wrist/palm/finger/ROI coordinates | **Yes, after spatial mapping** |
| Tissue | architecture, histology | **No — deeper data needed** |
| Cellular | morphology, cell state | **No — cellular-resolution data needed** |
| Molecular | RNA, biochemical/molecular values | **No — molecular/non-image data needed** |
| Longitudinal | change over time | **No from one timepoint** |
| Biological interpretation | disease/ageing state | **No from current RGB geometry alone** |

### Biological level hierarchy

The project should use the following conceptual hierarchy:

```text
ORGANISM
   │
   └── ORGANISM FRAGMENT
          │
          └── ANATOMICAL REGION / ZONE
                 │
                 └── TISSUE
                        │
                        └── CELL POPULATION
                               │
                               └── CELL
                                      │
                                      └── CELL PROPERTIES
                                             │
                                             └── MOLECULAR STATE
```

The hand is therefore the first concrete **organism-fragment** in the system.

### Resolution rule

The system must never silently promote an observation from one level to another.

For example:

```text
RGB image
  → measured colour difference
  → surface-level observation

NOT:
  → cancerous cell
```

Similarly:

```text
RNA signature
  → molecular observation

NOT automatically:
  → abnormal tissue morphology
```

A deeper result requires deeper evidence.

---

## Observation → interpretation boundary

This boundary is part of all five stages.

### Observation

Something directly measured or reproducibly computed from available evidence.

Examples:

- `image_width = 554 px`
- `hand_count = 1`
- `index_tip_x = 0.63`
- `palm_width_normalized = 0.21`
- `region_R17_brightness = 0.72`
- `cell_count = 1842`
- `TP53_expression = ...`

### Derived feature

A deterministic or validated transformation of observations.

Examples:

- finger-to-palm ratio,
- asymmetry measure,
- change from personal baseline,
- regional texture feature.

### Interpretation

A biological statement requiring a validated model/reference/assay.

Examples:

- disease-associated pattern,
- ageing-associated pattern,
- pathological morphology,
- cellular senescence-compatible state.

### Forbidden shortcuts

The following are explicitly prohibited by the scientific contract:

- dataset name → biological conclusion,
- public dataset → user's subject,
- visual difference → disease,
- visual appearance → cellular age,
- cell morphology alone → cancer without appropriate validation,
- missing data → normal state,
- technical detection confidence → disease risk.

---

## Stage 1–5 completion criteria

Stages 1–5 are considered **scientifically defined** when the project has frozen the following:

- [x] target response is an evidence map rather than a single health score;
- [x] `hand/` source roles are explicit;
- [x] personal, benchmark and placeholder data are separated;
- [x] hand information is mapped from acquisition through molecular levels;
- [x] every information type has an explicit biological/technical level;
- [x] observation, feature and interpretation are separate;
- [x] missing evidence is a valid outcome;
- [x] disease and ageing remain separate dimensions;
- [x] future deeper analysis must attach to explicit spatial/sample provenance.

### What is deliberately NOT claimed

Completing stages 1–5 does **not** mean that the system can already detect cancer, estimate cellular age, diagnose disease, or reconstruct a biologically faithful digital twin. It means that the scientific target and information architecture are now defined well enough to implement those capabilities one by one and validate them properly.

## Immediate implementation consequence

The next implementation work should focus on making `own_cohort` produce a clean, reproducible macroscopic observation object with:

```text
source
subject/session/timepoint (when explicitly registered)
acquisition quality
hand detection
landmarks
geometry
stable zone IDs
provenance
uncertainty
```

The next deeper step is not a disease classifier. It is a **spatial digital-twin/ROI contract** that can later accept tissue, cellular and molecular evidence without inventing links.
