# Reference data for the Human Digital Twin

The project uses external scientific datasets as **reference sources**, not as substitutes for subject-specific observations.

## Registered references

See `datasets/reference_sources.json` for the machine-readable manifest.

- NIH 3D — 3DPX-017237: healthy adult human hand anatomical template.
- HuBMAP Data Portal: public multimodal spatial and single-cell human tissue data.
- Allen Institute for Cell Science: 3D cell imaging, segmentation, cell features and related molecular datasets.

## Data policy

1. The repository stores source metadata and provenance by default, not large external datasets.
2. A user may explicitly download or import a source into local storage.
3. Imported files must retain source/dataset/version/license metadata.
4. Reference data must never be silently converted into user observations.
5. Reference data must not generate user-specific health, disease, biological-age, trajectory or treatment claims without an appropriate validated model.
6. If a required source, measurement or model is absent, the Digital Twin reports `NOT ESTABLISHED`.

## Intended spatial flow

```text
Reference / User source
        ↓
SpatialSource
        ↓
SpatialAsset
        ↓
SpatialRegion
        ↓
Tissue / Cell / Molecular evidence
        ↓
Canonical State
```

## User-specific data

A user can provide their own `.glb`/`.gltf`, imaging, segmentation, annotations and metadata. Those data should be registered as `USER` provenance and kept separate from `REFERENCE` datasets.

## Important scientific boundary

A reference hand template provides geometry and registration context. A spatial single-cell dataset provides cell/tissue/molecular evidence in its own specimen context. Combining these sources in the UI does **not** create a validated biological mapping between them. Such a mapping requires an explicit registration/annotation method and provenance.
