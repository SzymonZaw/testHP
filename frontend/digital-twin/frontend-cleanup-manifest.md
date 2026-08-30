# Frontend cleanup manifest — next-cleanup

The current frontend contains several historical `v1`, `v2`, `debug`, `fix` and `stages-*` modules. They are **not deleted automatically** because the active bootstrap still loads selected legacy modules and deleting them could regress the viewer.

## Canonical owners

| Concern | Canonical owner | Legacy modules must not own state |
|---|---|---|
| Digital Twin identity / spatial core | `digital-twin-core.js` + `digital-twin-runtime.js` | feature-local twin objects |
| Backend result boundary | `backend-contracts.js` + `analysis-result-adapter.js` | ad-hoc API response mapping |
| UI state | `canonical-state.js` + `canonical-ui-runtime.js` | feature-local analysis state |
| Upload flow | `user-upload-wizard-v1.js` | independent upload state machines |
| Evidence/QC | canonical state + evidence pipeline | duplicated evidence summaries |
| Biological model status | `biological-model-status.js` | guessed/derived validation status |
| 3D semantic state | `twin-viewer-state-v1.js` | local health/age truth in renderer |

## Safe cleanup rule

1. Migrate a legacy module to the canonical owner.
2. Verify the integration path.
3. Remove the legacy module only after no bootstrap/import/reference remains.
4. Do not remove diagnostic modules until their replacement is proven.

This manifest intentionally records the migration boundary rather than pretending that legacy code is already unused.
