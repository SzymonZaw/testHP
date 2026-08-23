# Phase A — TWIN VIEWPORT DEBUG verification

## Scope
Diagnostic checklist for verifying the canonical region context without changing `main`.

## Current observed failures
- Viewport manager exposes legacy display target `Palm` while canonical spatial ID is `hand/palm`.
- Navigation events expose `target: Palm` with `spatial_id: hand/palm`.
- Evidence diagnostics report `27 total` but `0 target-linked` for the current `hand/palm` target.

## Required verification
1. Enter `Dłoń → Śródręcze`.
2. Confirm manager, selected target, contract and evidence target all resolve to `hand/palm`.
3. Navigate to each direct child and back to `Śródręcze`.
4. Confirm no target writer changes the canonical target back to `Palm`.
5. Confirm direct evidence is scoped to `hand/palm` and descendants are excluded unless explicitly requested.
6. Confirm `TARGET CHAIN / PROVENANCE` reports a consistent canonical chain.

## Acceptance criteria
`MANAGER = CONTRACT = SELECTED = EVIDENCE = hand/palm`, with user-facing label `Śródręcze`; direct scope excludes `hand/palm/*`; no `TARGET DRIFT` is reported.
