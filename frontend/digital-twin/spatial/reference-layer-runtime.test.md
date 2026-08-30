# Reference layer runtime smoke test

Expected browser flow:

1. Load `/digital-twin/index.html`.
2. `TestHPReferenceLayerRuntime` is available.
3. Dispatch `testhp:reference-layer-projection` with `{ referenceLayers: { tissue: [], cell: [], molecular: [] }, referenceDatasetIds: [] }`.
4. `window.TestHPReferenceLayers` reflects the projection.
5. `testhp:reference-layers-changed` is emitted.
6. Existing `TestHPSpatialRuntime.sync()` is invoked without replacing a personal asset.

The runtime deliberately does not fabricate tissue/cell geometry. External datasets remain reference-only until a real spatial registration is supplied.
