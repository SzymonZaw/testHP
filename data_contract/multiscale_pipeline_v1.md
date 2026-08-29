# TestHP Multiscale Data Contract v1

This document defines the target input/output interfaces for the digital-hand pipeline. It is a software/data specification, not a claim of clinical validity.

## 1. Hand imaging

User data can contain still images, video, and/or a metric 3D reconstruction. The acquisition package records laterality, anatomical site, timepoint and acquisition metadata. Still-image acquisition should use dorsal, palmar and side views where practical, a visible physical scale reference in at least one reference image, diffuse lighting, neutral background, full-hand visibility and enough resolution for the intended task. 3D data should be metric, identify units and coordinate system, and record reconstruction/calibration metadata when available.

Pipeline:

```text
images / video / 3D
        ↓
quality control
        ↓
hand detection + segmentation
        ↓
anatomical landmarks
        ↓
metric geometry / temporal features
        ↓
registration to canonical hand coordinates
        ↓
hand-level features + uncertainty
```

## 2. WSI / histology → cells → tissue

```text
WSI
 ↓
slide quality control
 ↓
tissue detection
 ↓
stain normalization when appropriate
 ↓
nuclei/cell segmentation
 ↓
cell instances
 ↓
cell-type assignment
 ↓
spatial localization
 ↓
cell neighborhoods / microenvironment
 ↓
tissue-region aggregation
 ↓
anatomical registration to hand region
```

Every derived cell keeps a link to its source slide, tissue, subject and timepoint. Cell type and segmentation confidence are retained rather than discarded.

## 3. Genomics → biological features

```text
genomic assay
 ↓
QC + normalization
 ↓
variant/feature extraction
 ↓
functional annotation
 ↓
biological feature representation
 ↓
model
 ↓
biological-state evidence + uncertainty
```

Genomic data are evidence/features; they are not by themselves a diagnosis.

## 4. Proteomics → biological features

```text
protein abundance / MS data
 ↓
QC + normalization
 ↓
protein identification/mapping
 ↓
pathway and functional features
 ↓
biological-state model
 ↓
state features + uncertainty
```

## 5. Epigenetics → biological features

```text
methylation / chromatin / histone data
 ↓
QC + normalization
 ↓
epigenetic feature extraction
 ↓
epigenetic age/state features
 ↓
biological model
 ↓
state + uncertainty
```

## 6. Biological age

The platform must not assume that a single universally valid biological-age model exists at cell, tissue, region or whole-hand level. Each estimator must declare its training population, tissue/context, feature set, model version, validation cohort and uncertainty/calibration metrics.

```text
available molecular / imaging / clinical features
                    ↓
             age-related features
                    ↓
          biological-age estimator
                    ↓
       estimated age + uncertainty interval
                    ↓
      model/version + evidence/provenance
```

Supported reporting levels: cell, tissue, anatomical region and hand. If evidence is insufficient for a level, return `unavailable` rather than inventing a value.

## 7. Healthy ↔ disease ground truth

```text
image / RNA / protein / epigenetic / clinical evidence
                         ↓
                    reference label
                         ↓
             healthy / disease / subtype
```

Ground truth must remain separate from predictions. A label should record its definition, source, reference timepoint, evidence and adjudication/confidence when available. Validation should use subject-level separation and external validation when possible.

## 8. One multiscale hand model

```text
                         HAND
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
           anatomy                   imaging
              │                         │
              └────────────┬────────────┘
                           ↓
                    canonical geometry
                           │
                           ↓
                         tissue
                           │
                           ↓
                         cells
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
            RNA         protein      epigenetics
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                    biological state
                           │
                    ┌──────┴──────┐
                    ↓             ↓
            biological age   health/disease
                    │             │
                    └──────┬──────┘
                           ↓
                 evidence + uncertainty
```

The canonical linking keys are `subject_id`, `hand_id`, `timepoint_id`, anatomical-region/tissue identifiers and molecular sample/cell identifiers. Missing modalities remain explicitly missing and lower available evidence; they are never silently imputed as observations.

## User package rule

The existing `user_input_spec_v1.json` remains the top-level package envelope. This document and `multiscale_input_requirements_v1.yaml` define what each `kind` means and what the processing pipeline expects.
