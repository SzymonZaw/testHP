# Yamanaka-factor reprogramming datasets

This directory contains **dataset manifests and analysis notes only**. Do not commit GEO/SRA matrices or other large biological data to Git.

## Recommended order

### 1. GSE148158 — first experiment
Human bulk RNA-seq, early OSKM response (48h/72h). Use this dataset to validate the basic pipeline:

```text
GEO → metadata → expression matrix → QC → PCA → OSKM response → marker programs
```

GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE148158

### 2. GSE297234 — longitudinal single-cell experiment
Human fibroblasts treated with Sendai-virus OSKM, with days 0, 3, 7 and 10. This is the main target for trajectory analysis and future cell-state modelling.

GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE297234

### 3. GSE28688 — lightweight time-course validation
Human HFF1 cells measured at 0h, 24h, 48h and 72h after OSKM transduction. This is useful when a small matrix is preferable for quick experiments.

GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE28688

## Local storage convention

Place downloaded files under:

```text
data/raw/rna/reprogramming/<GEO_ACCESSION>/
```

Processed objects should go under:

```text
data/processed/rna/reprogramming/<GEO_ACCESSION>/
```

Suggested metadata fields:

```text
accession
sample_id
donor_id
cell_type
condition
reprogramming_factors
timepoint
treatment
assay
organism
source_file
```

## Scientific boundary

The first implementation should report measurements and model-derived features, not declare a cell "reprogrammed". A useful initial question is:

> Can early expression patterns predict or distinguish later cell-state trajectories during OSKM reprogramming?

Any predictive result should be evaluated with held-out samples/donors and clearly separated from biological interpretation.
