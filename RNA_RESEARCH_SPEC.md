# RNA modality — research specification

## Scope

`data/raw/rna/` represents the **molecular/transcriptomic level**. It should describe molecular state rather than image appearance or tissue geometry.

The current datasets include `GSE130973`, `GSE226189`, `GSE281449` and `spatial_skin_atlas`. The current lightweight reader can inspect some text/tabular content, but it does not yet constitute a validated transcriptomic analysis.

## Scientific questions

The RNA layer should progressively determine:

1. Is the molecular file genuinely present, readable and correctly identified?
2. What samples, genes/features, units and metadata are available?
3. What molecular measurements can be reproduced from the data?
4. Which genes/pathways/programs differ from an appropriate reference?
5. Which ageing-related or disease-related molecular programs are supported?
6. If spatial/sample metadata exists, where do those molecular observations belong?
7. Can molecular findings be linked to a WSI/tissue region through explicit specimen/sample identifiers?

## Information map

| Level | Information | Result type |
|---|---|---|
| Input | file format, size, sample count, metadata | observation |
| Matrix | genes/features, samples, sparsity, numeric distributions | measurement |
| Expression | normalized expression / counts with units | measurement |
| Comparison | differential expression / effect size | derived result |
| Pathway | pathway/gene-set activity | derived result |
| Ageing | validated ageing-associated molecular program | interpretation |
| Disease | validated disease-associated molecular program | interpretation |
| Spatial | sample/region location | explicit relationship |

## Current data boundary

Current observations such as row counts and numeric ranges are useful for auditing the input, but they are **not** biological findings. A molecular conclusion requires correct parsing, normalization, sample metadata and a validated statistical/biological analysis.

## Analysis ladder

```text
R0  input audit
 ↓
R1  sample/feature metadata validation
 ↓
R2  matrix loading + quality control
 ↓
R3  normalization / transformation appropriate to assay
 ↓
R4  exploratory structure / clustering
 ↓
R5  differential expression or other defined comparison
 ↓
R6  pathway / gene-set analysis
 ↓
R7  ageing-related molecular analysis
 ↓
R8  disease-related molecular analysis
 ↓
R9  spatial/specimen linkage to WSI or other tissue evidence
 ↓
R10 longitudinal molecular change
```

## Disease and ageing remain separate

The molecular result should never collapse ageing and disease into one number. The eventual state should retain separate evidence dimensions, for example:

- reference/normal molecular state,
- ageing-associated program,
- disease-associated program,
- uncertainty,
- missing/conflicting evidence.

## Desired final result

For each analyzed molecular dataset/sample:

- sample/specimen identifier,
- assay type and units,
- QC status,
- measured molecular features,
- derived molecular programs,
- ageing-related evidence,
- disease-related evidence,
- spatial/specimen links if explicitly available,
- uncertainty,
- provenance and analysis version.

## Completion criterion

The RNA phase is ready for multimodal integration when molecular results are reproducible, sample identity is explicit, units and preprocessing are documented, and any connection to tissue/hand observations has a defensible specimen/sample/timepoint relationship.
