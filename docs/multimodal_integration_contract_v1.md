# Multimodal integration contract — Stage 13

## Purpose

The platform combines modalities only after each modality has produced a validated result under its own contract.

## Evidence graph

Conceptually:

```text
Subject
  └── Timepoint
       ├── Hand observation
       ├── Skin image / region
       ├── Tissue specimen / WSI region
       └── Molecular sample / spatial region
```

A node may exist without all modalities being present.

## Integration rules

1. Integrate observations, not raw assumptions.
2. Preserve the original modality-specific result.
3. Store the explicit relationship that justified the connection.
4. Preserve conflicting evidence instead of silently resolving it.
5. Keep disease and ageing dimensions independent.
6. Mark missing evidence as missing, never as normal.
7. Do not infer cellular or molecular state from macroscopic appearance alone.

## Integration examples

### Hand → skin region

Requires explicit anatomical mapping or a registered spatial coordinate system.

### Skin image → WSI

Requires a defensible specimen/site relationship and preferably spatial registration. A photograph and a slide from similarly named datasets are not automatically the same sample.

### WSI → RNA

Requires explicit sample/specimen linkage or another validated pairing. A shared dataset topic is not enough.

### RNA → ageing/disease state

Requires a validated molecular endpoint, appropriate reference/comparison design and documented preprocessing.

## Digital twin role

The digital twin is the spatial/temporal index of evidence. It should reference measurements and analyses rather than inventing biological state.

## Integration output

For every cross-modal result store:

- source observation IDs,
- linkage method,
- spatial relationship if applicable,
- time relationship,
- derived feature,
- uncertainty,
- analysis version,
- validation status.
