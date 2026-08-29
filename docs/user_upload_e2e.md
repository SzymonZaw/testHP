# User upload → evidence flow

## Goal

A user submits one canonical v1 package. The API validates the package metadata, reports exactly which modalities are present, and never invents missing evidence.

## Current API

`POST /api/user-input/validate`

Request body:

```json
{
  "package": {
    "contract_version": "1.0",
    "subject": {"subject_id": "user-001"},
    "acquisition": {
      "timepoint_id": "T0",
      "acquisition_time": "2026-08-29T10:00:00Z",
      "laterality": "right"
    },
    "inputs": [
      {
        "input_id": "hand-front",
        "kind": "hand_images",
        "uri": "uploads/hand-front.jpg",
        "format": "jpg",
        "provenance": {"source_type": "user"}
      }
    ]
  }
}
```

The validator is metadata-only. `uri` is declared but not opened; local `data/raw` is not scanned and the database is not queried. This is deliberate: validation of the user's package must not silently depend on whatever research files happen to be present on a developer machine.

## Expected response semantics

- `valid`: package metadata satisfies the contract.
- `available_modalities`: modalities explicitly supplied by the user.
- `missing_modalities`: modalities not supplied; these remain unavailable.
- `evidence_status`: `observed`, `ground_truth`, or `unavailable` at this validation layer.
- `policy.missing_data_fabricated`: always `false`.

## Next physical-ingestion step

The next implementation should add a separate upload/ingestion service that:

1. accepts the declared files,
2. calculates SHA-256 checksums,
3. verifies file format and basic integrity,
4. creates canonical asset records,
5. binds assets to `subject_id` and `timepoint_id`,
6. emits provenance and quality metadata,
7. then invokes modality-specific pipelines.

It should not change the validation contract or infer unavailable modalities.
