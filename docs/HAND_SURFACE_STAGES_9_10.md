# Hand Surface · Stages 9–10

## Stage 9 — Surface projection
- Introduces a real hand-surface projection contract instead of treating photographs as flat overlays.
- Keeps source photographs, registration landmarks, camera metadata and derived surface textures separate.
- Defines multi-view blending weights and a surface-space observation coordinate.
- `projected` means the rendering projection exists; it does not claim validated anatomical registration.

## Stage 10 — Anatomical scaffold
- Adds an explicit deep anatomical scaffold layer for bones, joints, tendons and vessels.
- Scaffold visibility/opacity is independent from skin imagery and evidence overlays.
- Deep structures remain spatial context; rendering them does not create biological evidence.
- Input ownership remains with the active viewport layer so hidden/context layers cannot intercept clicks.

## Rendering contract

`REAL SKIN SURFACE → ANATOMICAL SCAFFOLD → EVIDENCE OVERLAY → DEEP DRILL`

The layers may coexist visually, but only the active interaction owner receives input.

Registration confidence, biological evidence and rendering state remain separate.
