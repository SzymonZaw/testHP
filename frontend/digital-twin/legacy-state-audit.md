# Legacy state audit — ETAP 22

The canonical state is the only owner of analysis-derived values. Existing feature modules are treated as legacy integration points until explicitly migrated.

| Domain | Canonical owner | Legacy policy |
|---|---|---|
| Evidence / QC | `state.evidence`, `state.qc` | no local result state |
| Health | `state.health` + anatomy | no local health conclusion |
| Biological age | `state.biologicalAge` | no UI-generated age |
| Molecular | `state.molecular` | no local interpretation |
| Cells | `state.anatomy.cells` | no local biological inference |
| Intervention | `state.interventions` | no local recommendation |
| 3D semantic data | canonical projections | renderer-only local selection allowed |

Searches on the current branch found no React `useState` usage and no direct `fetch(` match in the repository search index. Existing vanilla feature modules remain and must be migrated incrementally rather than deleted blindly.

A local UI selection (for example, selected region, open tab, camera position or wizard step) is presentation state and may remain local. An analysis-derived value is not presentation state and must come from `DigitalTwinState`.
