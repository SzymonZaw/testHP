# Biological Observation Model

This branch establishes the domain boundary for the long-term monitoring system.

## Principle

A dataset is a source of evidence. It is not the central biological entity.

The system models:

```text
Person / Subject
  -> Timepoint
  -> Anatomical location / zone
  -> Artifact
  -> Measurement
  -> Observation
  -> Evidence
  -> Digital Twin State
```

The same structure supports macro images, video, depth, microscopy, WSI, RNA/tabular values, and other non-image data.

## Separation of biological dimensions

Ageing and pathology must remain separate state dimensions. The domain model therefore does not encode a single `health_score` as the source of truth. A future analysis layer can combine evidence into risk or investigation priorities while preserving the underlying dimensions, for example:

- `cell_age`
- `damage`
- `pathology`
- `inflammation`
- `senescence`
- `cancer_probability`

The current model is descriptive and traceable; it does not diagnose disease.

## Hand vertical slice

The existing `backend.multiscale_pipeline` already provides conservative evidence extraction from hand images and media. `backend.hand_observation_adapter` maps those records into the core domain model without changing their interpretation.

```text
data/raw/hand/own_cohort
        |
        v
multiscale_pipeline
        |
        v
EvidenceRecord
        |
        +--> Artifact
        +--> Measurement
        +--> Observation
        |
        v
DigitalTwinState
        |
        v
zone / timepoint history
```

This is the first integration boundary for the future hand digital twin. It intentionally does not claim that a simple RGB image can establish cellular age or pathology. Those dimensions become available only when the relevant evidence exists.

## Raw directory semantics

`data/raw/hand` is an anatomical-domain input area, not one homogeneous dataset. It may contain multiple modalities and data levels over time. In particular:

- `own_cohort/` is for the user's own test/longitudinal observations;
- `media/` is for user's hand video/media;
- `InterHand2_6M/` is external reference/training data and must not be treated as the user's subject.

`images/`, `rna/`, and `wsi/` remain separate source domains. Their artifacts can later be linked to the same subject/timepoint when the acquisition metadata establishes that relationship.

## Next integration steps

1. Add a formal subject/session/timepoint ingestion contract for `raw/hand`.
2. Make the dataset registry reference artifacts rather than define biological identity.
3. Integrate hand zone ontology with `DigitalTwinState`.
4. Add validation that distinguishes external reference datasets from own-cohort observations.
5. Run the first end-to-end T0 hand ingestion and expose zone-level investigation priorities in the dashboard.
6. Add micro/cellular and non-image evidence as additional modalities without changing the core identity model.
