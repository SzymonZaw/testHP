# Reference Cell Data Model

The spatial reference layer uses a conservative cell-level contract. Fields that cannot be established from the source dataset remain `null`; the model must not infer health, pathology, or biological age from a spatial coordinate alone.

## Canonical shape

```json
{
  "cellId": "...",
  "anatomicSite": "forearm",
  "regionName": "region_3",
  "x": 735.067,
  "y": 1418.026,
  "cellType": null,
  "cellSubtype": null,
  "healthState": null,
  "biologicalAge": null,
  "confidence": {}
}
```

## Semantics

- `cellId`: source cell identifier.
- `anatomicSite`: source anatomical site; this is not a registration to the NIH hand model.
- `regionName`: source dataset region label when available.
- `x`, `y`: source `obsm["spatial"]` coordinates.
- `cellType`, `cellSubtype`: reserved for source-derived cell annotations.
- `healthState`: reserved for a separately validated health/pathology model; do not populate from location alone.
- `biologicalAge`: reserved for a separately validated aging model; do not equate it with donor chronological age.
- `confidence`: explicit model/source confidence values only.

## Spatial boundary

The current reference extract remains in `sample_local` coordinate space and is `unregistered_to_hand`. No coordinates in this model imply a correspondence with a particular location on the 3D NIH hand geometry.

## Design rule

The viewer may expose these fields at progressively finer zoom levels, but unknown biological states must remain unknown rather than being replaced by guesses. This keeps the visualization layer separate from future health, pathology, and aging estimators.
