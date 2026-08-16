# Branch strategy

`main` is the source of truth for the current project, current own-cohort data, documentation, and reproducible pipeline state.

## Keep

- `main` — current integrated project and personal test data.
- `agent/stages-26-34-multimodal` — retained as a development/history line until its useful changes are fully integrated into `main`.
- `agent/hand-own-cohort-structure-v1` — retained as historical reference for the Hand ontology/Digital Twin implementation; no new work should start here.
- `agent/framework`
- `agent/web-framework`
- `agent/research-dashboard`
- `agent/research-output`

The last four are separate historical UI/framework experiments.

## Deprecated

Do not develop further on these branches:

- `agent/hand-own-cohort`
- `agent/hand-own-cohort-v2`
- `agent/hand-own-cohort-v3`
- `agent/hand-own-cohort-v4`
- `agent/hand-own-cohort-v5`
- `agent/hand-own-cohort-v6`
- `agent/hand-own-cohort-v7`
- `agent/hand-analysis-images-v1`
- `agent/stages-21-25`
- `complete-stage-4`
- `integration/hand-own-cohort-main`
- `agent/test-fixtures-v1`
- `agent/real-analyses`

The redundant `v2`–`v6` refs represent the same historical state and can be deleted once local clones no longer depend on them.

## Data rule

Personal input data belongs on `main` under `data/raw/hand/own_cohort/` and `data/raw/hand/media/`. Development branches should not become alternative sources of truth for personal data.

## New work

Use short-lived feature branches from current `main`, for example:

- `feature/hand-observations`
- `feature/hand-video`
- `feature/images-skin`
- `feature/wsi-analysis`
- `feature/rna-analysis`
- `feature/multimodal-fusion`

Avoid numbered copies such as `v2`, `v3`, `v4`, etc.
