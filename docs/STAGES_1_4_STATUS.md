# Digital Twin stages 1-4

## Status

Stages 1-4 are integrated on the `development` branch.

### Stage 1 — Spatial Digital Twin

The existing Hand Digital Twin remains the spatial foundation:

`Hand → region/finger → segment → tissue/field → cell target`

Spatial navigation and drill-up/drill-down remain the source of truth for the selected target.

### Stage 2 — Evidence Management

`POST /api/spatial/attach` attaches an uploaded asset to a canonical spatial node and records:

- subject
- timepoint
- spatial node and spatial level
- modality
- resolution
- source
- filename/path
- creation time
- explicit research signals

The attachment registry is runtime state under `data/registry/spatial_evidence.json`; it is not a dataset committed to Git.

Additional read endpoints:

- `GET /api/spatial/registry`
- `GET /api/spatial/tree`

### Stage 3 — Current Biological State

`GET /api/spatial/state` returns the state that is supported by evidence attached directly to the selected node.

Supported explicit research signals include:

- macro: `macro_age`, `skin_age`, `wrinkles`, `elasticity`, `pigmentation`
- tissue: `tissue_age`, `fibrosis`, `inflammation`, `collagen_structure`
- cellular: `cell_age`, `health_score`, `stress_score`, `senescence_score`, `cell_count`
- molecular: `molecular_age`, `inflammaging`, `biomarkers`, `gene_signatures`

Age values are labelled `research_proxy` and are never produced when the corresponding explicit evidence is absent.

The system therefore returns `not_established` / `insufficient_evidence` rather than inventing a biological conclusion.

### Stage 4 — Hierarchical Biological Summary

`POST /api/spatial/summary` aggregates explicitly attached descendant evidence through the selected spatial path.

Example:

```text
hand
  → palm
    → thenar
      → field-b
        → cell-3
```

A summary at `hand/palm/thenar` can use evidence attached to that node and its descendants. It cannot create evidence at a deeper level that has not been supplied.

Numeric signals are summarized as observed means with an evidence count. Explicit age signals are summarized independently by layer and, when multiple layer ages are present, an overall research proxy is reported.

## UI

The Hand Digital Twin now exposes:

1. an Evidence Management panel for file + metadata + optional structured research signals,
2. a Current Biological State panel driven by `/api/spatial/state`,
3. a Hierarchical Summary panel driven by `/api/spatial/summary`.

The UI maps human-readable spatial breadcrumbs to canonical node IDs, including segment, microscopy-field and cell-target drill-down paths.

## Example structured signals

```json
{
  "macro_age": 41,
  "wrinkles": 32,
  "elasticity": 74,
  "tissue_age": 43,
  "fibrosis": 12,
  "inflammation": 18,
  "cell_age": 42,
  "health_score": 81,
  "stress_score": 21,
  "senescence_score": 14,
  "cell_count": 324,
  "molecular_age": 44,
  "inflammaging": 27
}
```

These values are explicit research inputs for the prototype. They are not clinically validated measurements.
