# Hand evidence contract v1

## Stage 6 — Observation vs interpretation

The hand pipeline must separate three classes of output.

### Observation
Directly supported by an input and an executed deterministic analysis.

Examples: dimensions, readable frames, hand detected/not detected, landmark coordinates, geometry, region coverage, colour/brightness/texture statistics, depth, motion, tissue measurements, cell counts, or molecular values when the required evidence exists.

### Derived feature
A deterministic or validated transformation of observations that does not claim a biological cause.

Examples: finger-length ratios, palm/finger proportions, asymmetry, range-of-motion features, longitudinal change and spatial priority scores.

### Interpretation
A biological statement requiring validated reference data, an appropriate model or assay, and evidence that supports the claim.

Examples: disease-related abnormality, tumour-related evidence, inflammation, cellular senescence, cellular age, disease risk or biological ageing.

The platform must never silently promote an observation or derived feature into an interpretation.

### Required result envelope

Every result should carry `subject_id`, `session_id`, `timepoint`, `source_id`, optional `region`, `biological_level`, `result_type`, `metric`, `value`, `unit`, `uncertainty`, `status` and `provenance`.

`status` should distinguish at least `available`, `partial`, `unavailable` and `not_applicable`.

### Hard boundary
A difference from a public dataset is not itself a disease finding. Public benchmark data must never be linked to the personal subject without an explicit shared identifier. Missing evidence must never be interpreted as normality.

## Stage 7 — Analysis ladder

1. Input integrity and file discovery.
2. Acquisition quality.
3. Hand localization and landmarks.
4. Geometry and proportions.
5. Surface descriptors.
6. Functional/temporal analysis when video/depth exists.
7. Spatial zoning and ROI mapping.
8. Deviation/priority ranking without disease claims.
9. Tissue analysis when microscopy/WSI/equivalent evidence exists.
10. Cellular analysis when cell-resolution evidence or validated assays exist.
11. Molecular/non-image analysis when such evidence exists.
12. Multimodal interpretation after explicit subject/spatial links and validation.
13. Longitudinal comparison for the same explicit subject.

A level is inactive rather than fabricated when its evidence is absent.

## Stage 8 — First hand result contract

The first personal implementation should produce:

- acquisition and quality observations;
- hand detection status;
- landmark geometry;
- a canonical hand coordinate system;
- seven initial regions: wrist, palm, thumb, index, middle, ring, little;
- per-region coverage and measurements;
- macroscopic colour/brightness/texture descriptors;
- temporal features when real media is available;
- explicit missing-evidence records for tissue, cellular and molecular levels.

It should support the future digital twin and progressive zoom, but it must not claim disease, pathology or cell age.
