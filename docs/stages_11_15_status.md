# Stages 11–15 — completion status

This document freezes the scientific definition for the RNA modality and the transition from modality-specific analysis toward stable data contracts, multimodal integration, validation, and research-interface requirements.

## Stage 11 — RNA audit

`data/raw/rna/` is the molecular/transcriptomic layer. The current repository-facing audit identifies four intended sources:

- `GSE130973`
- `GSE226189`
- `GSE281449`
- `spatial_skin_atlas`

The current lightweight run can count files, rows and finite numeric values, but those counts are **input observations only**. They do not establish a valid expression matrix, normalization, biological effect, ageing program or disease program.

Important current evidence from the run:

- `GSE130973`: 2 tabular/text files, 2106 counted data rows, 0 finite numeric values in the inspected content.
- `GSE226189`: 5 tabular/text files, 2201 counted data rows, 3868 finite numeric values, observed range 0–154774938.
- `GSE281449`: 2 tabular/text files, 1033 counted data rows, 0 finite numeric values in the inspected content.
- `spatial_skin_atlas`: 3 tabular/text files, 566 counted data rows, 20 finite numeric values, observed range 4200585–4271950.

These findings mean the next implementation must first identify the actual assay/file schema before attempting transcriptomic statistics.

## Stage 12 — stable data contracts

Every observation entering the unified system must carry, where available:

- subject ID,
- sample/specimen ID,
- anatomical site,
- spatial zone or coordinate system,
- acquisition timestamp/timepoint,
- modality and assay type,
- source dataset and version,
- file/source identifier,
- units and preprocessing state,
- quality flags,
- analysis/model version,
- provenance,
- uncertainty.

Missing identifiers remain missing. The system must not manufacture links from filenames, folder names or dataset labels.

## Stage 13 — modality-specific pipelines

Each modality must have an explicit contract:

`input → validation → preprocessing → measurement → derived features → interpretation boundary → provenance`

The first validated implementations are expected to be descriptive and modality-specific. Biological claims become available only after the corresponding method is validated.

## Stage 14 — research interface

The interface must expose the evidence path rather than only a final score. A researcher should be able to:

1. load or register data,
2. inspect detected inputs and quality,
3. see which analyses are available,
4. inspect observations and derived features,
5. select a region/sample for deeper analysis,
6. inspect explicit cross-modal links,
7. compare timepoints,
8. inspect provenance and limitations,
9. export the run record.

## Stage 15 — scientific validation and prospective path

Validation is a separate stage from model development. The platform must support benchmark datasets, held-out validation, reproducibility checks, uncertainty reporting, failure-mode analysis, and eventually external/prospective validation where scientifically and clinically appropriate.

No current implementation should be presented as a diagnostic system.

## Completion state

Stages 11–15 are scientifically specified. They do not claim that all future biological analyses have already been implemented. The next engineering work is to implement and validate the modality-specific pipelines against these contracts, beginning with the real RNA schemas and then connecting them to the existing hand/images/WSI evidence model.
