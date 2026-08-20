# Region Inspector / Observation Management contract

## Single data relationship

The canonical relationship is:

```text
Region → Evidence → Observation
```

An observation is spatially explicit through `spatial_id` and may point to an `evidence_id`. The Region Inspector reads observations filtered by the selected spatial node; the global Observation Manager reads the same registry without being a second region-specific data store.

## Region Inspector

Question answered: **What do we know about this region?**

Responsibilities:
- current region context and spatial path,
- evidence/data availability,
- observations belonging to the selected region,
- compact observation counts by biological level,
- opening observation details without leaving the region workflow.

## Observation Manager

Question answered: **Which observations do we manage?**

Responsibilities:
- global observation register,
- search and filters,
- sorting and tabular browsing,
- editing and version history,
- audit trail and provenance fields.

It must use the same `/api/observations` registry as the Region Inspector.

## Boundary rule

The Region Inspector must not create a second observation store. `region-data-manager.js` remains responsible for legacy evidence/data cards; `observation-manager.js` and `region-observation-inspector.js` operate on the biological observation registry.
