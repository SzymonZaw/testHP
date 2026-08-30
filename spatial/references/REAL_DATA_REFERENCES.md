# Real spatial data references

This directory contains references to external scientific datasets. Large external assets are intentionally not vendored into the repository.

## 1. Human hand reference asset

**NIH 3D Print Exchange — 3DPX-017237**

- URL: https://3d.nih.gov/entries/3DPX-017237
- Asset: 3D anatomical template of a healthy adult human hand.
- Source: T1-weighted MR images from 27 healthy adult hands / 21 subjects.
- Processed with ANTs and segmented/exported with 3D Slicer.
- The published entry provides an STL and supplemental documentation; the processed version history may also provide GLB-compatible output.
- Important limitation: this is a real anatomical reference, not a guaranteed semantic segmentation of `palm`, `thumb`, `index`, `middle`, `ring`, `little`, and `wrist`. Those IDs must only be asserted after a validated segmentation/annotation is available.

Original research/template repository:
https://github.com/HegdeUSA/Hand_template

## 2. Human spatial/cellular reference

**HuBMAP Human Reference Atlas (HRA)**

- URL: https://humanatlas.io/
- Documentation: https://docs.humanatlas.io/dev
- Data portal: https://hubmapconsortium.org/hubmap-data/
- HRA provides a multiscale 3D reference framework, anatomical structures, cell types, biomarkers, spatial positions, and registration/provenance concepts.
- HuBMAP data can be searched and, where permitted, downloaded for local processing.
- The HRA/CCF is a reference framework, not evidence that a particular user's hand contains the same cells or measurements.

## 3. Spatial single-cell visualization/reference tooling

HuBMAP's tooling includes the Exploration User Interface and Vitessce for spatially registered single-cell datasets. These are useful interoperability references for future `tissueId`, `cellId`, coordinates, segmentation and molecular layers.

## 4. Data policy for this project

The application must distinguish:

1. `reference` — public atlas/template data;
2. `user` — data supplied by the individual user;
3. `observed` — measurements actually attached to that subject/timepoint;
4. `computed` / `estimated` / `predicted` — values produced by an explicitly identified model;
5. `not_established` — no supported result exists.

A reference hand must never silently become a user's personal hand. A reference cell must never be presented as a measured cell from the user's subject.

## 5. Intended spatial chain

```text
External reference or user upload
        ↓
SpatialAsset
        ↓
geometryId
        ↓
validated annotation / segmentation
        ↓
regionId
        ↓
tissueId
        ↓
cellId + coordinates
        ↓
evidence
        ↓
molecular observations
```

## 6. Recommended next acquisition

For a true hand Digital Twin, the next scientific-data milestone is a hand dataset with validated anatomical segmentation and spatial registration. The NIH template is a strong geometric baseline, while HRA/HuBMAP supplies the multiscale vocabulary and spatial-data concepts. Neither source alone should be treated as a complete personal hand twin.
