# Spatial reference sources

Reference datasets are external scientific sources. They are not treated as user biological data and are never used to invent health, age, disease, confidence, or trajectory results.

## NIH3D healthy adult hand template

- Dataset: `3DPX-017237`
- Source: https://3d.nih.gov/entries/3DPX-017237
- Role: reference anatomical geometry / registration template
- Provenance: constructed from T1-weighted MR images of 27 healthy adult hands from 21 subjects
- Important limitation: this is a population-derived anatomical template, not the user's hand and not cell-level biological evidence.

## NIH3D segmented hand/wrist bones

- Dataset: `3DPX-017249`
- Source: https://3d.nih.gov/entries/3DPX-017249
- Role: reference segmented bone geometry
- License listed by NIH3D: GPLv3
- Important limitation: represents bones only; it does not establish tissue, cell, health, age, or disease state.

## PALM

- Source repository: https://github.com/facebookresearch/PALM
- Role: research/reference dataset for real captured hand geometry and appearance
- Published dataset description: 263 subjects, about 90k multi-view RGB images and about 13k 3dMD hand scans with MANO registrations
- Access: dataset download requires registration according to the project documentation
- Important limitation: external research data; it must not be silently presented as the current user's anatomy.

## Application policy

The application may expose these sources as `reference` SpatialSources and use them to validate the spatial pipeline. User-owned data remains a separate `user_upload`/`own_dataset` source. Every spatial asset must retain provenance and source identity.

A reference source may provide geometry and coordinates. It does not provide validated biological age, health, disease state, intervention recommendations, or clinical confidence for the user.
