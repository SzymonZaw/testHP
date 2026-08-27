# Hand data contract

This module is the frontend contract for layer-owned hand data. It does not render UI and does not replace the existing geometry renderer.

## Ownership

A layer owns its geometry, measurements, images, observations and projection metadata. Consumers should not infer ownership from whichever layer happens to be selected in the UI.

## Source priority

When resolving a value, the intended priority is:

1. `real` — user/measurement-derived data
2. `computed` — derived/reconstructed data
3. `default` — fallback data

The priority is a data-resolution rule, not permission to silently mix classic and real-hand modes.

## Image spatial contract

Every image assigned to a layer carries a stable `spatial.layerId`. A surface-projected image must also carry a coordinate system and transform. Changing the currently selected depth/layer must not rewrite these fields.

## Photo pipeline

`upload -> source -> view-assignment -> preparation -> registration -> surface-projection`

Each stage is represented by status rather than by implicit UI state.

## Real mode

`canUseRealMode()` only answers whether real data exists. It does not manufacture missing geometry. The mode switch remains responsible for the user's explicit classic/real choice.
