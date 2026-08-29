# Scientific integrations

`dev/next-cleanup` now treats external scientific projects as replaceable
providers rather than reimplementing their models inside testHP.

## Enabled integration map

| # | Provider | Role in testHP | Integration status |
|---:|---|---|---|
| 1 | Human Cell Atlas (HCA) | reference single-cell/spatial data | catalog + metadata descriptor |
| 2 | CZ CELLxGENE | reference single-cell data | query descriptor |
| 3 | Cellpose-SAM | microscopy cell segmentation | runnable lazy adapter |
| 4 | UNI2 | WSI/pathology embeddings | model handle |
| 5 | scGPT | single-cell representation | model handle |
| 6 | Geneformer | second single-cell representation | model handle |
| 7 | scGPT-spatial | spatial omics representation | model handle |
| 8 | Arc Virtual Cell Atlas | reference/perturbation data | catalog descriptor |
| 9 | u-Segment3D | 3D cellular representation | model handle |
| 10 | AlphaFold DB | protein-structure knowledge | entry URL/provenance helper |

## Architecture rule

External providers produce observations, embeddings, masks or reference data.
They do not directly produce a clinical decision. The result must pass through
testHP evidence, provenance, uncertainty and biological-state layers.

```text
external provider
      ↓
provider adapter
      ↓
testHP observation/evidence contract
      ↓
provenance + uncertainty
      ↓
biological state / twin
```

## Dependencies and weights

Do not commit model weights or large datasets to Git. The core dependency list
already contains Cellpose; the other model families are intentionally optional
and loaded only in environments where their upstream dependencies and weights
have been installed.

Before redistributing or deploying any model, verify the license/terms of the
specific upstream code, checkpoint and dataset version. A provider being listed
here does not imply that every checkpoint is freely redistributable.

## Current scope

This change establishes the integration boundary and reusable provider
contracts. It does **not** claim that any external model is clinically valid or
that testHP can currently diagnose disease or calculate a validated biological
age. Benchmarking, calibration and independent validation remain required.
