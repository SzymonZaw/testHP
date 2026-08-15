# Hand input data audit

## Purpose

This document records the first audit of `data/raw/hand/` and defines what should be extracted from the current inputs before implementing deeper biological analysis.

The hand modality is a future personal-data entry point for the digital biological twin. It must therefore support both ordinary camera/video data and future higher-dimensional data, including microscopy, 3D/depth observations and non-image measurements.

## Current repository contents

The current branch contains three sources:

```text
data/raw/hand/
├── InterHand2_6M/
├── media/
└── own_cohort/
```

### 1. `own_cohort/`

Currently contains three JPEG files:

- `1.jpg` — 12,186 bytes
- `2.jpg` — 13,098 bytes
- `3.jpg` — 9,487 bytes

These are the most important files for the eventual personal-data workflow. They should be treated as **observations of one research subject only if that identity/relationship is explicitly recorded by the run metadata**. File names alone must not create subject links.

For the first implementation we should extract only directly measurable properties: image dimensions, readability, colour/raster statistics, hand localisation/segmentation, orientation, visible surface features and, where validated, geometric landmarks.

We should not infer disease, ageing or cellular state from these three photographs.

### 2. `media/`

Currently contains:

- `test.mp4` — 0 bytes
- `test2.mp4` — 0 bytes

These are placeholders and currently contain no usable video evidence. The system should report them as unavailable/empty rather than attempting analysis.

The intended future role is broader: video should support temporal observations such as hand movement, range of motion, stability, velocity, symmetry and repeatability. If future recordings include depth or other sensor channels, these should become separate modality-specific observations rather than being hidden inside a generic video result.

### 3. `InterHand2_6M/`

The repository currently contains a test subset organised under:

```text
data/raw/hand/InterHand2_6M/images/
├── Info.txt
├── InterHand2.6M_test_MANO_NeuralAnnot.json
├── InterHand2.6M_test_joint_3d.json
└── test/
    └── Capture0/
        └── ROM01_No_Interaction_2_Hand/
            ├── cam400262/
            └── cam400263/
```

`Info.txt` explicitly points to an additional `InterHand2.6M_test_data.json` file. The two large JSON files are approximately 12.3 MB and 15.9 MB respectively in the repository metadata.

The names indicate that this source contains substantially richer information than ordinary photographs: 3D hand-joint annotations and MANO/neural annotations. The `test` hierarchy also identifies a capture and a recording/action context (`ROM01_No_Interaction_2_Hand`) and multiple camera streams.

This makes InterHand2_6M particularly useful as a **reference and algorithm-development dataset** for the hand reconstruction layer. It should not be treated as personal cohort data.

## What we can reasonably extract

The first target is a hierarchy of measurable observations, not a medical diagnosis.

| Level | Candidate observation | Current source | Status |
|---|---|---|---|
| Input | file existence/readability/format/size | all | implement now |
| Image | width/height/aspect ratio | `own_cohort`, InterHand images when present | implement now |
| Image | colour/raster statistics | `own_cohort`, image streams | implement now |
| Hand | hand bounding region / segmentation | photographs/video | next |
| Hand | orientation and pose | `own_cohort`, InterHand2_6M | next |
| Hand | anatomical landmarks | InterHand2_6M | reference implementation |
| Hand | 3D joint coordinates | InterHand2_6M | reference implementation |
| Hand | geometric proportions | image/3D | next |
| Region | finger/palm/wrist zones | image/3D | next |
| Motion | range of motion | video / annotated sequences | future |
| Motion | velocity/stability/repeatability | video | future |
| Surface | local texture/colour/visible lesion candidates | ordinary images | future, evidence-only |
| Tissue | microscopic morphology | future microscopy/WSI | future |
| Cell | cell morphology/state | future microscopy | future |
| Molecular | non-image molecular measurements | future hand-associated data | future |
| Longitudinal | change from previous observations | all linked observations | future |

## Important distinction: observation vs interpretation

The hand pipeline should preserve the following separation:

```text
MEASUREMENT
    ↓
FEATURE
    ↓
DEVIATION / AREA OF INTEREST
    ↓
HYPOTHESIS
    ↓
DEEPER MEASUREMENT
    ↓
BIOLOGICAL INTERPRETATION
```

For example:

```text
Measured: a region has a different colour/texture
        ↓
Observed: region differs from the person's previous baseline
        ↓
Research action: inspect that region more closely
        ↓
Possible next input: high-resolution image / microscopy / WSI / molecular data
        ↓
Only then: validated pathological or ageing interpretation
```

A visual difference must never automatically become a disease claim.

## Progressive analysis architecture

The hand should become the first practical demonstration of the project's progressive-resolution concept:

```text
ordinary image / video
        ↓
whole-hand state
        ↓
spatial zones
        ↓
selected region
        ↓
higher-resolution tissue observation
        ↓
cellular observation
        ↓
molecular / non-image measurement
```

The digital twin should eventually provide the spatial identity used to connect these observations. A deeper measurement should be attached to a region only when the relationship between the measurements is explicitly established.

## Scientific-definition checklist

The previously agreed first eight steps are now completed for `hand/`:

- [x] 1. Define the target system response — a spatially organized evidence map, not a single health score.
- [x] 2. Audit `raw/hand` — `own_cohort`, empty `media` placeholders and external `InterHand2_6M` reference data are documented.
- [x] 3. Define the role of each source — personal evidence, future media entry point, and external algorithm-development reference are separated.
- [x] 4. Build the hand information map — input, image, hand, region, tissue, cell and molecular/non-image levels are defined.
- [x] 5. Define biological level for each information type — macroscopic, regional, tissue, cellular and molecular levels are explicit.
- [x] 6. Separate observation from interpretation — measurements/features/ROIs are kept separate from disease/ageing interpretation.
- [x] 7. Define the analysis ladder — H0–H11 progressive analysis is specified in `HAND_RESEARCH_SPEC.md`.
- [x] 8. Define the hand outputs — the result contract and success criteria are specified in `HAND_RESEARCH_SPEC.md`.

This checklist means the **scientific definition phase** is complete. It does not mean that every H-level analysis has already been implemented.

## What to implement next

### Phase H1 — Complete data inventory

For every file under `raw/hand`, record:

- path,
- modality,
- format,
- byte size,
- readability,
- dimensions,
- frame count where applicable,
- timestamp where available,
- subject identifier if explicitly provided,
- capture/session identifier,
- anatomical region if explicitly provided,
- annotation availability,
- provenance.

The inventory must distinguish **empty placeholders** from usable data.

### Phase H2 — InterHand2_6M adapter

Build a read-only adapter that can understand the available InterHand test annotations and expose them through the common observation model.

The first outputs should be transparent:

- number of annotated samples,
- number of hands,
- available cameras,
- available 2D/3D landmarks,
- coordinate conventions/units if available,
- annotation completeness,
- capture/action identifiers.

### Phase H3 — Personal image adapter

Build the first `own_cohort` analysis around actual measurements:

1. image validation,
2. hand detection/segmentation,
3. orientation,
4. landmark estimation,
5. geometric measurements,
6. spatial zoning,
7. quality score.

Do not add disease or ageing classifiers at this stage.

### Phase H4 — Personal hand digital twin v0

Create a spatial representation of the hand that can contain:

- palm,
- wrist,
- fingers,
- joints,
- configurable regions of interest,
- observation history,
- measurement provenance,
- uncertainty.

The first version can be anatomical and geometric rather than biologically predictive.

### Phase H5 — Region-of-interest workflow

The system should be able to say:

> This region is different or uncertain; inspect it next.

The user should be able to select that region and attach a higher-resolution observation later.

### Phase H6 — Video adapter

Only after usable video is present, implement temporal analysis:

- frame quality,
- hand tracking,
- pose trajectory,
- range of motion,
- movement speed,
- stability,
- symmetry,
- repeatability.

### Phase H7 — Deep-resolution interfaces

Define interfaces for future:

- microscopy,
- WSI,
- cellular measurements,
- molecular/non-image data.

The important part at this stage is the **linking contract**: how a deep measurement is associated with a specific hand/region/timepoint without inventing a relationship.

## Current conclusion

The current `hand` data are sufficient to start building the **data and spatial architecture**, but not sufficient for biological conclusions.

The most useful immediate work is therefore:

```text
inventory
  ↓
InterHand2_6M reference adapter
  ↓
own_cohort image measurements
  ↓
hand landmarks + geometry
  ↓
spatial hand model
  ↓
region-of-interest selection
  ↓
interfaces for deeper modalities
```

The empty MP4 files should remain explicitly marked as unavailable until real recordings are supplied. The current InterHand JSON annotations should be used as reference material for reconstructing the type of rich hand observations the future system should support, while `own_cohort` remains the path toward the user's personal digital twin.
