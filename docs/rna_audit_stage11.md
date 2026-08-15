# RNA audit — Stage 11

## Role

`data/raw/rna/` is the molecular/transcriptomic layer. It is not an image layer and it should not be used to infer tissue morphology without an explicit relationship to tissue data.

## Current sources

| Source | Current run evidence | Immediate interpretation |
|---|---|---|
| GSE130973 | 2 tabular/text files; 2106 data rows; 0 finite numeric values in inspected content | schema/content must be identified before expression analysis |
| GSE226189 | 5 tabular/text files; 2201 data rows; 3868 finite numeric values; range 0–154774938 | numeric content exists, but assay units/normalization must be established |
| GSE281449 | 2 tabular/text files; 1033 data rows; 0 finite numeric values in inspected content | schema/content must be identified before expression analysis |
| spatial_skin_atlas | 3 tabular/text files; 566 data rows; 20 finite numeric values; range 4200585–4271950 | likely contains metadata/limited numeric content; actual schema must be established |

These are measurements of repository input, not biological findings.

## What must be established for each dataset

1. Assay type: bulk RNA-seq, single-cell, spatial transcriptomics, microarray or another assay.
2. Matrix orientation: genes × samples or samples × genes.
3. Feature identifiers: gene symbols, Ensembl IDs, probes or other IDs.
4. Sample identifiers and subject/specimen identifiers.
5. Measurement units: counts, TPM, FPKM, normalized intensity, log-expression or another scale.
6. Missing values and filtering rules.
7. Experimental groups and covariates.
8. Tissue/anatomical site.
9. Batch information.
10. Spatial coordinates or region identifiers where available.
11. Whether the source can be linked to WSI or another modality.

## Research outputs

The RNA pipeline should eventually produce:

- QC observations,
- expression/molecular measurements,
- reproducible comparisons,
- differential-expression results where justified,
- pathway/gene-set results,
- ageing-associated molecular evidence,
- disease-associated molecular evidence,
- explicit spatial/specimen links,
- longitudinal molecular change,
- uncertainty and provenance.

## Hard boundary

Do not report a disease or ageing conclusion from row counts, numeric ranges, dataset names or unvalidated gene lists. Do not claim cellular age from ordinary expression data without a validated endpoint.
