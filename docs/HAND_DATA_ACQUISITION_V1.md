# Hand data acquisition v1

This contract defines the smallest repeatable acquisition unit for the Hand Digital Twin. It is deliberately independent of any particular imaging device so that the project can start with a phone and microscope and later add USG/HFUS, OCT, or molecular evidence.

## Acquisition hierarchy

```text
subject
  -> session
    -> timepoint
      -> modality acquisition
        -> artifact(s)
          -> measurements / observations
```

Every acquisition should preserve these identifiers:

- `subject_id` — who/what the observation belongs to;
- `session_id` — one acquisition session;
- `timepoint_id` — longitudinal position such as `T0`, `T1`;
- `acquired_at` — ISO-8601 timestamp;
- `modality` — e.g. `phone_image`, `microscopy`, `hfus`, `oct`, `wsi`, `rna`;
- `source_uri` — path or external URI;
- `region_id` — optional anatomical target;
- `source_role` — `own_cohort` or `reference`;
- `device` / `protocol_id` — optional acquisition details;
- `quality` — acquisition-quality information;
- `provenance` — processing/source metadata.

## Why this comes before prediction

The project must be able to add a future modality without changing biological identity. A later HFUS or OCT measurement should attach to the same subject/timepoint/region as the phone and microscopy observations when the acquisition metadata establishes that relationship.

The system must never infer identity from similarity alone. If a cross-modality link is not explicitly established, the evidence remains separate.

## Initial repeatable protocol

For a local longitudinal pilot, use a fixed protocol rather than maximizing the number of measurements:

1. Capture front and back hand photos under repeatable lighting and distance.
2. Record the same anatomical regions at every timepoint.
3. Capture a small fixed set of microscopy fields from the same regions.
4. Record acquisition metadata and quality notes.
5. Keep raw artifacts outside Git when they are large or personal.
6. Generate derived measurements without replacing the original evidence.
7. Repeat at a fixed cadence to create T0, T1, T2, ...

## Modality ladder

```text
NOW
  phone image
  microscopy

LATER / OPTIONAL
  depth / 3D
  USG
  HFUS
  OCT

REFERENCE / RESEARCH
  histology / WSI
  single-cell RNA
  spatial transcriptomics
  spatial proteomics
```

The absence of a later modality is **not** a negative biological finding. It is `insufficient evidence` for that modality-dependent dimension.

## Future prediction boundary

Models may estimate deeper properties from cheap observations only when the model is trained and evaluated against appropriate reference measurements. Predictions must retain:

- model/version;
- training/reference cohort;
- input modalities;
- uncertainty/calibration information;
- anatomical scope;
- evidence links.

A prediction is not a measurement and must never silently replace missing HFUS/OCT/cellular evidence.

## Implementation target

The first software milestone is a validated `HandAcquisition` record and tests. The next milestone is to connect it to the existing hand observation adapter and make T0 ingestion produce stable acquisition identifiers.
