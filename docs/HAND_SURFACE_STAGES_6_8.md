# Hand Surface · Stages 6–8

## Stage 6 — Landmark-assisted registration
- Defines stable hand landmarks in normalized hand space.
- Exposes registration metadata separately from biological evidence.
- Provides an inspectable landmark overlay.
- Status is explicitly `landmark-assisted`; this is not a claim of clinical-grade registration.

## Stage 7 — Texture atlas
- Combines available multi-view photographs into a deterministic 2048×2048 atlas.
- Records the exact source views used.
- Keeps the atlas as a derived rendering asset; originals remain the evidence source.
- `built` means the atlas was generated, not that anatomical registration is validated.

## Stage 8 — Spatial observation overlays
- Loads registered observations for the current subject/timepoint when available.
- Places observations as spatial markers in normalized hand coordinates.
- Markers are an evidence-navigation layer, not new biological findings.
- Overlay interaction is separate from the 3D hand input layer.

## Contract

`RAW IMAGE → MULTI-VIEW → LANDMARK REGISTRATION → ATLAS → SPATIAL OBSERVATION`

No stage creates evidence merely by rendering geometry. Registration confidence and evidence availability remain separate state.
