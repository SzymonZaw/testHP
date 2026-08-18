# Spatial node state contract

The Digital Twin viewport consumes one canonical state per selected spatial node:

- `resolution`: `macro`, `tissue`, `cellular`, or `cell`
- `target`: current spatial target
- `path`: ordered spatial ancestry
- `parent`: immediate parent target
- `children`: next drill-down targets
- `evidence`: evidence explicitly linked to the current node/resolution

A renderer must never infer evidence from a sibling, ancestor, or unrelated asset merely because it is available. Missing evidence means navigation-only state.
