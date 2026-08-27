# Digital Twin — Phase A: Data Foundation

Status: specification baseline for `dev/next-cleanup`.

## Goal

Define the minimum data foundation for a longitudinal, multimodal, spatially registered hand digital twin. The 3D model is a derived representation; observations remain traceable to their acquisition source.

## 1. Data Dictionary

Every data object must declare:

- `data_type` — image, 3d_scan, measurement, observation, imaging_volume, tissue_sample, histology, cell_data, omics, etc.
- `subject_id`
- `hand_id` — left/right hand identity where applicable
- `timepoint_id`
- `acquisition_id`
- `source_type` — user, device, laboratory, imported, derived
- `modality`
- `spatial_reference` — coordinate system / anatomical target
- `status`
- `quality`
- `uncertainty`
- `provenance`
- `created_at`
- `derived_from` for computed data

### Core classes

| Class | Examples | Primary nature |
|---|---|---|
| image | hand photo, microscopy image | observed |
| 3d_scan | surface scan, point cloud | observed / processed |
| measurement | length, circumference, grip strength | observed |
| observation | visible lesion, color change | observed |
| imaging_volume | MRI, 3D ultrasound | observed |
| tissue_sample | biopsy/sample metadata | observed |
| histology | H&E, IHC, IF | observed |
| cell_data | segmented cells, morphology | derived / observed |
| omics | RNA, protein, epigenetic data | observed / processed |

## 2. Subject / Hand / Timepoint

The identity hierarchy is:

```text
Subject
└── Hand (left/right)
    └── Timepoint
        └── Acquisition
            └── Data objects
```

A timepoint is a first-class entity. No measurement, image, reconstruction or biological assessment should exist without a traceable timepoint (unless explicitly marked as historical/unknown).

Suggested timepoint metadata:

- `timepoint_id`
- nominal date/time
- age at acquisition
- reason/protocol
- fasting/rest/activity context where relevant
- clinical context when permitted

## 3. Provenance

Every derived object must retain its lineage:

```text
raw acquisition
  -> preparation
  -> processing
  -> registration
  -> reconstruction / analysis
  -> derived result
```

At minimum provenance records:

- source object IDs
- method / algorithm name and version
- software/pipeline version
- parameters/configuration
- operator/device where relevant
- processing timestamp
- parent spatial reference
- validation/QC result

Raw source data must not be overwritten by preparation or analysis.

## 4. Quality and confidence

Separate **data quality** from **biological confidence**.

### Acquisition quality

Examples:

- completeness
- resolution
- exposure / motion quality
- calibration validity
- registration quality
- artifact flags

### Interpretation confidence

Examples:

- evidence count
- classifier confidence
- agreement between modalities
- validation status
- uncertainty interval / score

`quality` must never be silently interpreted as `health`.

## 5. Spatial Coordinate System

The project needs a stable hand-centric spatial reference independent of the currently visible UI layer.

Conceptually:

```text
HAND_REFERENCE_FRAME
├── surface coordinates
├── anatomical landmarks
├── depth / volumetric coordinates
└── registered modality transforms
```

Every spatially meaningful object should identify:

- coordinate frame
- anatomical target
- transform from acquisition space
- registration status
- registration quality

Changing a visualization layer must never mutate the spatial location of source evidence.

## Source classification

Use an explicit source class instead of inferring it from module names or filenames:

```text
observed   = directly acquired from a person/device/sample
computed   = calculated from observed data
default    = reference/fallback value
simulated  = synthetic/research data
```

The system must preserve the distinction between these classes through every downstream representation.

## Minimum acceptance criteria for Phase A

1. A photo can be traced to subject → hand → timepoint → acquisition.
2. A derived 3D surface can be traced back to its source images/scans.
3. Every spatial object declares its coordinate reference and registration state.
4. Raw and processed data are distinct objects.
5. Quality and uncertainty are explicit and not conflated with biological state.
6. Longitudinal comparisons can identify the exact timepoints being compared.
7. Observed, computed, default and simulated values cannot be silently mixed.
8. Missing data is represented explicitly; absence is not replaced by a fabricated default without declaring it.

## Scope boundary

Phase A does not define diagnostic algorithms, biological-age formulas, treatment recommendations, or clinical decisions. It defines the data foundation needed to support those later stages safely and reproducibly.
