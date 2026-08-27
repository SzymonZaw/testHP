# Multiscale Hand Digital Twin

## Purpose

The project models a hand digital twin from person-level identity down to tissue
and cell observations. Interpretations such as cell state or biological age are
derived claims and must never replace the underlying observations and evidence.

## Canonical hierarchy

```text
Subject
  -> Hand
    -> Timepoint
      -> Acquisition
        -> Dataset / Observation
          -> Anatomical structure
            -> Tissue region
              -> Histology / microscopy
                -> Cell
```

## Evidence-first interpretation

Every biological interpretation follows:

```text
Observation -> Evidence -> Interpretation
```

Interpretations carry:

- target object identity;
- source/evidence object IDs;
- provenance and processing method/version;
- confidence;
- explicit uncertainty;
- assessment timestamp.

The repository currently provides contracts for `BiologicalStateAssessment`
and `BiologicalAgeEstimate` in `backend/biological_state.py`. These contracts
do not diagnose disease and do not prescribe treatment.

## Longitudinal model

The same subject/hand should be observable across multiple timepoints. Future
models should compare trajectories rather than treating a single image as a
complete biological state.

```text
T0 -> T1 -> T2 -> ... -> Tn
 |     |     |
 observations, tissues, cells, assessments
```

## Future decision-support boundary

The eventual system may support research-oriented comparison of current and
predicted states and identify areas that merit review. It must preserve the
distinction between measured evidence, model inference, uncertainty and any
human clinical decision.

The intended progression is:

1. canonical data and provenance;
2. real-data ingestion;
3. spatial registration;
4. multiview hand reconstruction;
5. tissue representation;
6. cell segmentation and tracking;
7. cell morphology features;
8. validated health-state models;
9. validated biological-age models;
10. longitudinal trajectory models;
11. research/clinical decision-support evaluation.
