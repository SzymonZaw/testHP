# Branch strategy

`main` is the source of truth for the current project, current own-cohort data, documentation, and reproducible pipeline state.

## Current branches

- `main` — current integrated project and personal test data.
- `agent/stages-26-34-multimodal` — historical/development line containing the stages 26–34 multimodal implementation. Its useful changes should be reviewed and integrated into `main`; no new work should start here.
- `agent/framework` — historical UI/framework experiment.
- `agent/web-framework` — historical web-framework experiment.
- `agent/research-dashboard` — historical dashboard experiment.
- `agent/research-output` — historical research-output experiment.

## Data rule

Personal input data belongs on `main` under `data/raw/hand/own_cohort/` and `data/raw/hand/media/`. Development branches are not alternative sources of truth for personal data.

## Integration policy

The `agent/stages-26-34-multimodal` branch diverged substantially from `main` (119 commits ahead and 32 behind at the time of this audit). It must therefore **not** be force-merged or used to replace `main` wholesale. The correct approach is a reviewed integration of its useful files/commits while preserving the current `main` data and newer project state.

## New work

After integration, use short-lived feature branches from current `main`, for example:

- `feature/hand-observations`
- `feature/hand-video`
- `feature/images-skin`
- `feature/wsi-analysis`
- `feature/rna-analysis`
- `feature/multimodal-fusion`

Avoid numbered copies such as `v2`, `v3`, `v4`, etc.
