# Stage 15 — legacy cleanup boundary

The spatial integration now has one canonical identity path:

`Observation -> PhotoAsset -> PreparedPhoto -> RegisteredView -> ReconstructionAsset -> SpatialObject`

Legacy rules:

- no new module may introduce a second spatial-object identity;
- `localStorage` may be used only for UI convenience, never as reconstruction persistence;
- OBJ/MTL/PNG are artifacts of a `ReconstructionAsset`, not independent domain entities;
- view names must use the canonical set: `front`, `back`, `side_left`, `side_right`, `thumb`;
- hand preparation/landmarks/coordinate normalization belong to Hand Surface;
- Photo 3D consumes Hand Surface evidence rather than reimplementing it;
- Inspector and Navigation consume `SpatialObject` rather than reconstruction-specific IDs.

Existing compatibility adapters are retained until their consumers are migrated. New code must not extend the legacy contracts.
