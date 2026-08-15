# Hand modality — data contract and analysis ladder

## Purpose

`data/raw/hand/` is the prototype entry point for the future **individual hand monitoring pipeline**. It is not limited to ordinary photographs. The long-term design must accept multiple levels of evidence about the same anatomical region, from ordinary camera/video observations through depth/3D data, microscopy or pathology images, and non-image molecular/biophysical measurements.

The hand is therefore treated as a **test anatomical region for the complete platform**. Once the pipeline works reliably, the same architecture should be reusable for other body regions.

## Current audit

The repository currently contains three sources:

| Source | Role | Current state | What it can contribute now |
|---|---|---|---|
| `own_cohort/` | User-owned test input | 3 JPEG images, non-empty | Basic image-level observations and future personal longitudinal tests |
| `media/` | User-owned video input | 2 MP4 placeholders, both 0 bytes | No valid video analysis yet |
| `InterHand2_6M/` | External reference/benchmark | Annotation JSON files plus a small test hierarchy | Hand pose/landmark/3D-structure research and model benchmarking |

The current `media/` files are placeholders and must not be interpreted as usable recordings. `own_cohort/` contains real image files and can be used as a prototype input, but a few photographs are not enough to establish a longitudinal or biological conclusion.

`InterHand2_6M` is **not the user's biological data**. It should be treated as an external reference/benchmark source. Its annotation files include 3D joint information and MANO/neural annotations; these are useful for learning and validating hand geometry/pose processing, not for making health claims about the user.

## What the hand pipeline should eventually answer

The final system should not return one unexplained "hand health score". It should progressively answer:

1. **What was observed?**
   - image/video quality
   - hand visibility and completeness
   - pose and orientation
   - geometry and proportions
   - skin-visible characteristics
   - motion characteristics
   - depth/3D structure when available
   - deeper tissue/cellular/molecular measurements when available

2. **Where is the observation located?**
   - anatomical region
   - hand side
   - finger/palm/dorsum/wrist region
   - eventually a stable 3D anatomical coordinate system

3. **Is the observation reliable?**
   - acquisition quality
   - missing regions
   - blur/occlusion/lighting
   - modality compatibility
   - measurement uncertainty

4. **Is anything unusual?**
   - deviation from the person's own baseline
   - deviation from an appropriate reference cohort
   - temporal change
   - spatially localised anomaly

5. **What requires closer examination?**
   - identify a region of interest
   - request or consume a more appropriate modality
   - escalate from macro-scale to micro-scale only when evidence supports it

6. **What can responsibly be interpreted?**
   - separate direct measurements from model-derived inference
   - distinguish ageing-associated signals from pathology-associated signals
   - allow `insufficient_evidence` when the available data cannot support a conclusion

## Information map

The hand should be represented as a hierarchy rather than as a flat collection of files.

```text
HAND
├── acquisition
│   ├── image
│   ├── video
│   ├── depth / RGB-D
│   └── other sensors
├── anatomy / geometry
│   ├── hand pose
│   ├── joints / landmarks
│   ├── surface geometry
│   ├── proportions
│   └── anatomical regions
├── function
│   ├── movement
│   ├── range of motion
│   ├── symmetry
│   └── temporal dynamics
├── visible tissue / skin
│   ├── colour / texture
│   ├── lesions or structural changes
│   └── longitudinal change
├── tissue / cellular
│   ├── microscopy
│   ├── histology / pathology
│   ├── cell morphology
│   └── cell-state measurements
└── molecular / non-image
    ├── transcriptomic measurements
    ├── biochemical measurements
    ├── molecular markers
    └── other quantitative observations
```

## Biological levels

Every hand observation should declare its biological level:

| Level | Example evidence | Typical output |
|---|---|---|
| Acquisition | JPEG/MP4/RGB-D | quality, coverage, metadata |
| Macroscopic | ordinary hand image/video | visible morphology, colour, geometry |
| Functional | video / pose sequence | motion, range of motion, stability |
| Tissue | WSI / microscopy | tissue morphology and architecture |
| Cellular | microscopy / cell analysis | cell morphology, counts, abnormality candidates |
| Molecular | RNA / biochemical values | molecular expression or quantitative markers |
| Longitudinal | repeated measurements | trend, change point, personal baseline deviation |

The system must not silently jump from one level to another. A macroscopic image cannot by itself establish a cellular diagnosis.

## Observation vs interpretation

### Observation

An observation is directly computed or read from the input, for example:

- image dimensions;
- number of visible hands/fingers;
- 2D or 3D joint coordinates;
- measured range of motion;
- pixel/colour statistics;
- segmentation geometry;
- cell count or morphology measurement;
- RNA expression value.

### Interpretation

An interpretation is a model- or rule-derived statement, for example:

- possible asymmetry;
- possible abnormal motion;
- possible lesion candidate;
- possible age-associated change;
- possible pathological signal.

Interpretations must retain their evidence references, method/model version, confidence/uncertainty and limitations.

## Analysis ladder

The hand pipeline should be implemented in this order:

```text
L0  ingest + provenance
 ↓
L1  quality + coverage
 ↓
L2  hand detection + localisation
 ↓
L3  anatomical landmarks / 3D pose
 ↓
L4  region segmentation
 ↓
L5  macro morphology / visible-skin analysis
 ↓
L6  temporal / functional analysis
 ↓
L7  deeper tissue analysis when WSI/microscopy exists
 ↓
L8  cellular analysis when cellular-resolution data exists
 ↓
L9  molecular / non-image analysis
 ↓
L10 multimodal fusion for the same anatomical region
 ↓
L11 longitudinal personal baseline + change detection
 ↓
L12 digital-twin update + targeted next measurement
```

A later level must never be fabricated when the required evidence is absent.

## Digital-twin role

The digital twin should eventually contain a stable representation of the hand and its regions. A useful progression is:

```text
photographs / video
       ↓
hand detection
       ↓
3D pose / surface reconstruction
       ↓
anatomical coordinate system
       ↓
hand regions / zones
       ↓
region-level observations
       ↓
flagged regions
       ↓
request / analyse deeper evidence
       ↓
tissue / cellular / molecular state
       ↓
update longitudinal hand state
```

The important design point is that a flagged region is **not automatically diseased**. It means that the available evidence justifies closer measurement or review.

## Role of current datasets

### `own_cohort/`

This is the future personal input path. For the prototype it should be used to validate the ingestion and macroscopic analysis pipeline. In a real longitudinal setup, files should eventually carry or be associated with:

- subject identifier;
- acquisition timestamp;
- hand side;
- anatomical view;
- acquisition device;
- acquisition conditions;
- optional depth/sensor metadata;
- region or session identifier.

### `media/`

This is the future dynamic/functional input path. It should accept real videos and eventually other temporal sensor streams. The first useful analyses are not pathology claims; they are temporal observations such as hand detection, tracking, pose, motion, range of motion and repeatability.

### `InterHand2_6M/`

This is a reference/benchmark source. It is valuable for training/testing hand detection, pose estimation, joint localisation and 3D reconstruction components. It should remain conceptually separate from `own_cohort` so that benchmark data are never mistaken for the user's measurements.

## Immediate implementation order

1. Keep the current raw data audit visible in the dashboard.
2. Implement a `hand` ingestion object with provenance and source role (`personal`, `benchmark`, `placeholder`).
3. Implement acquisition quality and coverage checks.
4. Implement basic hand detection/localisation on `own_cohort`.
5. Use `InterHand2_6M` only for pose/geometry benchmarking.
6. Replace the empty MP4 placeholders with a real test video before implementing video-derived results.
7. Implement anatomical landmarks and a stable hand coordinate system.
8. Implement region segmentation/zoning.
9. Define the first real macro-scale measurements.
10. Add longitudinal identity/timepoint handling before claiming change over time.
11. Only then connect deeper WSI/microscopy/RNA evidence to a hand region.
12. Only after modality-specific validation should pathology/ageing interpretations be exposed.

## Non-negotiable boundaries

- Empty files are unavailable evidence, not negative findings.
- Benchmark data are not personal data.
- A visible difference is not automatically pathology.
- Ageing and pathology are separate hypotheses that require separate evidence.
- Cellular age cannot be inferred from ordinary hand photographs.
- A digital twin is a structured representation of evidence, not proof that the virtual reconstruction is biologically identical to the real tissue.
- Multimodal fusion requires explicit linkage to the same subject, anatomical region and relevant timepoint.
- When evidence is inadequate, the correct output is `insufficient_evidence` or a request for a better measurement.
