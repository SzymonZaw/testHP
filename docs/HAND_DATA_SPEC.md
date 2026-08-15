# Hand data specification

## Purpose

`data/raw/hand/` is the first practical entry point for the future multimodal monitoring workflow. It is not limited to ordinary hand photographs. The long-term target is to monitor one investigated fragment across multiple scales, from macroscopic appearance and movement to tissue, cellular and non-image measurements.

The hand is therefore the first test object for the architecture of a future digital biological twin.

## Current audit

| Source | Current contents | Role now | Role later |
|---|---|---|---|
| `InterHand2_6M/` | 6 JPG images + 2 JSON annotation files in the current test subset | External reference/benchmark for hand pose and spatial understanding | Reference data for training/validation of hand geometry, landmarks and zone mapping; **not** evidence about the researcher's own hand |
| `own_cohort/` | 3 JPG images | Own-subject input test set | Main entry point for repeated observations of the investigated hand/cohort |
| `media/` | 2 empty MP4 files | Placeholder only; no video can currently be analyzed | Temporal RGB/depth/video observations for movement, deformation, surface change and longitudinal monitoring |

The current repository evidence confirms that `own_cohort/` contains three non-empty JPG files, while both current MP4 files in `media/` are zero bytes. `InterHand2_6M/` contains a small external reference subset with image and JSON annotation data. citehttps://github.com/SzymonZaw/testHP/tree/agent/real-analyses/data/raw/hand

## Important distinction: reference data vs subject data

`InterHand2_6M` must remain a reference/benchmark source. It can teach or validate geometric and pose-related processing, but it must never be treated as if it were an observation of the user's own hand.

`own_cohort` is the future longitudinal subject/cohort input. It should eventually carry explicit identifiers, visit/time information, acquisition metadata and anatomical/spatial references.

`media` is currently only a placeholder. Empty video files must be reported as unavailable input, not as successful video analysis.

## What we want to extract from hand data

The analysis should be layered. We should not jump directly from a photograph to a biological conclusion.

### Level 1 — acquisition and quality

First determine whether the input is usable:

- file integrity,
- image/video dimensions,
- frame rate and duration for video,
- exposure and saturation,
- blur/focus quality,
- occlusion,
- viewpoint,
- lighting consistency,
- depth availability and quality,
- metadata and acquisition conditions.

**Output:** quality/coverage observations and an explicit statement of what analysis is possible.

### Level 2 — hand detection and geometry

From ordinary images/video:

- detect the hand,
- estimate hand mask,
- identify left/right hand where possible,
- estimate landmarks and joints,
- estimate pose and orientation,
- normalize scale and viewpoint where justified,
- construct a stable anatomical coordinate system.

InterHand2_6M is useful primarily at this level because its annotations provide reference information for hand geometry and pose.

**Output:** measured geometry and pose, not disease claims.

### Level 3 — anatomical zoning

Create a persistent hand coordinate system and divide it into meaningful regions, for example:

- wrist,
- palm,
- thenar/hypothenar areas,
- dorsal hand,
- individual fingers,
- joints,
- nails,
- predefined skin zones.

The exact zoning scheme should be defined scientifically before implementation. Zones should have stable IDs so that observations from different visits and modalities can be attached to the same region.

**Output:** a spatial map that can become the first layer of the digital twin.

### Level 4 — visible surface observations

For RGB/depth imagery, extract validated descriptive features such as:

- colour statistics,
- texture descriptors,
- surface geometry,
- local asymmetry,
- visible lesions or regions of interest,
- swelling/deformation indicators,
- temporal changes,
- movement characteristics.

These remain **observations/features** until a validated model establishes a biological interpretation.

### Level 5 — region-of-interest detection

Use broad measurements to identify regions that deserve deeper analysis.

The desired workflow is:

```text
whole hand
   ↓
zone-level measurements
   ↓
regions of interest
   ↓
select region
   ↓
request higher-resolution evidence
```

A region should be flagged because measured evidence deviates from a defined reference or changes over time, not merely because a dataset/model predicts that it is interesting.

### Level 6 — deeper tissue/cellular evidence

Future hand observations may include microscopy, tissue images, cellular measurements, numerical laboratory data or molecular measurements linked to a hand region.

At that point the system can progressively move toward:

```text
hand zone
   ↓
tissue region
   ↓
cell population
   ↓
individual cell
   ↓
cell properties
   ↓
molecular state
```

The existence of this path does **not** mean that a normal photograph can establish cellular age or cancer. Each deeper claim requires the appropriate evidence and a validated modality-specific analysis.

## Research result categories

The final hand workflow should separate at least four layers:

### A. Direct measurements

Examples:

- hand/region dimensions,
- joint/landmark coordinates,
- surface colour and texture statistics,
- movement measurements,
- depth-derived geometry,
- cell counts when cellular data exist,
- numerical molecular values when molecular data exist.

### B. Derived features

Examples:

- asymmetry score,
- change from previous visit,
- deviation from a reference distribution,
- region-level anomaly score,
- morphological feature vectors.

### C. Research interpretations

Examples, only when validated analysis supports them:

- ageing-associated pattern,
- disease-associated pattern,
- tissue abnormality,
- cellular state.

### D. Unavailable / not established

Examples:

- no usable video,
- no tissue data for a flagged zone,
- no molecular data,
- no explicit subject link,
- insufficient validation for a biological claim.

This distinction is essential. **No evidence is not evidence of normality.**

## Disease and ageing remain separate

For any future hand region we should preserve independent evidence dimensions:

```text
Disease-related evidence
        ×
Ageing-related evidence
```

A region could therefore be:

- no detected abnormality in available evidence,
- ageing-associated evidence without disease-associated evidence,
- disease-associated evidence without strong ageing evidence,
- evidence for both,
- or insufficient evidence.

These are research states, not diagnoses.

At cellular resolution the long-term question can be formulated as:

> Does this cell show evidence compatible with a pathological state, an ageing-related state, both, or neither, given the validated evidence available for that cell?

A separate "cell age" output should only be implemented if the project obtains a validated method and suitable reference data for estimating biological/cellular age.

## Digital twin requirements derived from hand

The hand workflow gives us the first concrete requirements for the digital twin:

1. persistent subject/fragment identity,
2. anatomical coordinate system,
3. stable zone IDs,
4. observation timestamps,
5. acquisition metadata,
6. modality and resolution metadata,
7. links between observations and zones,
8. links from macroscopic regions to deeper samples when explicit identifiers exist,
9. longitudinal history,
10. provenance and analysis version for every derived result.

The twin is therefore primarily an **evidence organization model**, with visualization built on top of it.

## Proposed hand analysis ladder

The implementation order should be:

```text
1. input/quality validation
        ↓
2. hand detection
        ↓
3. landmarks + pose
        ↓
4. anatomical coordinate system
        ↓
5. persistent zones
        ↓
6. surface measurements
        ↓
7. longitudinal comparison
        ↓
8. region-of-interest prioritization
        ↓
9. deeper tissue/cellular analysis when evidence exists
        ↓
10. molecular/non-image integration when explicit links exist
        ↓
11. disease/ageing interpretation with validation
```

## What should be implemented next

The next coding step should **not** be a disease classifier.

It should be a formal hand observation contract that can consume `own_cohort` and produce:

- file/quality status,
- detected hand geometry,
- anatomical zones,
- measurable observations per zone,
- provenance,
- explicit unavailable-analysis reasons,
- and a structure ready to accept future depth/video/tissue/cellular/RNA evidence.

After that contract works on the current three own-cohort images, the same pipeline can be extended to real video and richer data.
