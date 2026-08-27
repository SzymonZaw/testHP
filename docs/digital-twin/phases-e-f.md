# Phase E + F — Cell and molecular data

## Phase E — Cell

### 17. Cell segmentation

Microscopy segmentation creates cell-level objects only when the segmentation result points to source images and a parent tissue region. Segmentation confidence/quality is retained separately from biological interpretation.

### 18. Cell identity

`CellIdentity` records the proposed cell type, marker evidence and confidence. A type is not treated as ground truth merely because a classifier produced it.

### 19. Cell morphology

`CellMorphology` stores measurable morphology: size, shape and nucleus features, plus segmentation quality and evidence IDs. Measurements remain distinguishable from interpretation.

### 20. Cell state

`CellState` records states such as normal, stressed, senescent, apoptotic, proliferating, inflammatory, pathological or unknown. Every assessment requires evidence, provenance, time and optional confidence.

## Phase F — Molecules

### 21. scRNA-seq

`MolecularAssay` represents single-cell transcriptomic measurements with sample identity, subject/hand/timepoint, source data, feature space, quality and provenance. It can optionally carry a spatial reference when a defensible mapping exists.

### 22. Spatial transcriptomics

Spatial transcriptomic assays use the same molecular contract but must retain spatial reference information. A spot/grid coordinate is not silently treated as a cell coordinate; mapping requires explicit evidence.

### 23. Proteomics

Proteomic measurements are represented as molecular assays with an explicit feature space and source sample. Protein abundance is kept separate from transcript abundance and from downstream biological interpretation.

### 24. Epigenetics

Epigenetic assays use the same provenance and identity model. The feature space identifies the assay representation (for example methylation or chromatin-related measurements) instead of collapsing all epigenetic data into one value.

### 25. Multi-omics integration

`MultiOmicsLink` joins at least two assays using an explicit alignment space, optional cell/region IDs, method, confidence and provenance. It does not assume that assays from the same person are automatically spatially or temporally aligned.

## Critical lineage rule

```text
subject / hand / timepoint
          |
       tissue
          |
        cell
          |
   molecular assays
          |
    multi-omics link
```

Every integration must remain traceable to its source assays and sample IDs. Missing or uncertain mappings remain explicit instead of being filled with defaults.

## Biological-age boundary

These phases provide observations and evidence. They do not yet produce a definitive biological age, disease diagnosis, rejuvenation recommendation or treatment decision. Those require a separate validated inference layer with reference cohorts, uncertainty estimates, longitudinal validation and clinical governance.
