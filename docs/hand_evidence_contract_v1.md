# Hand evidence contract v1

This document freezes the boundary between what the hand pipeline can **observe**, what it can **derive as a feature**, and what would require a validated biological interpretation.

## Stage 6 — Observation vs interpretation

### Observation
A value directly supported by an input file and an executed deterministic analysis.

Examples: image dimensions, readable-frame count, hand detection, landmark coordinates, geometric measurements, region coverage, colour/brightness/texture statistics, explicit depth or motion measurements, and tissue/cellular/molecular measurements when the corresponding evidence and validated routine exist.

### Derived feature
A deterministic or validated transformation of observations that does not itself claim a biological cause.

Examples: finger-length ratios, palm-to-finger proportions, asymmetry indices, range-of-motion features, longitudinal change relative to baseline, and spatial priority scores based on measured deviations.

### Interpretation
A biological statement that requires validated reference data, model performance and appropriate evidence.

Examples: disease-related abnormality, tumour-related evidence, inflammation, cellular senescence, cellular age, disease risk or biological ageing state.

The system must never silently promote an observation or derived feature into an interpretation.

## Output schema

Every future hand result should carry:

| Field | Meaning |
|---|---|
| `subject_id` | Explicit investigated subject, if known |
| `session_id` | Acquisition session |
| `timepoint` | Longitudinal timepoint |
| `source_id` | Input source/file group |
| `region` | Spatial zone or ROI, if applicable |
| `biological_level` | acquisition, macro, region, tissue, cell, molecular, longitudinal |
| `result_type` | observation, derived_feature, interpretation |
| `metric` | Stable metric identifier |
| `value` | Numeric/string/structured value |
| `unit` | Unit where applicable |
| `uncertainty` | Confidence/error/quality information |
| `evidence_required` | Evidence needed for stronger claims |
| `status` | available, partial, unavailable, not_applicable |
| `provenance` | Analysis routine/version and source reference |

## Research-result boundary

The current hand system may report measured image/pose properties. It must not report a biological diagnosis merely because a value differs from a reference dataset. Public benchmark data must never be linked to the personal subject unless an explicit shared identifier exists.

## Stage 7 — Analysis ladder

The hand analysis should progress from cheap/broad evidence to expensive/deep evidence:

1. **Input integrity** — discover files, formats, readability, metadata.
2. **Acquisition quality** — dimensions, exposure/brightness, blur/coverage and other modality-specific quality checks.
3. **Hand localization** — detect hand and estimate landmarks where supported.
4. **Geometry** — orientation, proportions, distances, angles, contour and symmetry.
5. **Surface** — colour, brightness, texture and visible surface descriptors.
6. **Functional/temporal** — video/depth/temporal features when available.
7. **Spatial zoning** — map observations onto wrist, palm and digit regions; allow custom ROIs.
8. **Deviation/priority** — compare repeated observations or validated references and rank regions for closer inspection without calling the deviation a disease.
9. **Tissue** — activate only when microscopy/WSI/equivalent evidence exists.
10. **Cellular** — activate only when cell-resolution data or validated cellular assays exist.
11. **Molecular/non-image** — activate when molecular or numerical laboratory evidence exists.
12. **Multimodal interpretation** — only after explicit spatial/subject links and validated modality-specific models exist.
13. **Longitudinal state** — compare comparable sessions for the same explicit subject.

A higher level must never be fabricated when its evidence is missing.

## Stage 8 — Hand results to implement

The first implementation target is the personal macroscopic layer. It should produce:

- input-quality observations;
- hand detection status;
- landmark geometry;
- canonical hand coordinate system;
- seven initial regions: wrist, palm, thumb, index, middle, ring, little;
- per-region coverage and available observations;
- macroscopic colour/brightness/texture descriptors;
- optional temporal features when `media/` becomes real video;
- explicit missing-evidence records for tissue/cellular/molecular layers.

The output should be useful for the future digital twin but should not claim disease, cell age or pathology.

The next implementation can then attach deeper evidence to a selected region rather than analysing all deep modalities indiscriminately.
