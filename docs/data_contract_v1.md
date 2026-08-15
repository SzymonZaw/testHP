# Unified biological observation contract — Stage 12

The platform uses one evidence contract across hand, images, WSI, RNA and future modalities.

## Identity

Every record should preserve, when available:

- `subject_id`
- `session_id`
- `timepoint`
- `sample_id`
- `specimen_id`
- `anatomical_site`
- `spatial_zone_id`

Identifiers are explicit. Missing identifiers remain missing.

## Acquisition

- `modality`
- `assay_type`
- `source_dataset`
- `source_version`
- `file_id`
- `acquired_at`
- acquisition/device metadata

## Measurement

- `feature`
- `value`
- `unit`
- measurement scale / preprocessing state
- coordinate system where relevant

## Evidence state

- `evidence_type`: observation | derived_feature | interpretation
- `quality_status`
- `uncertainty`
- `validation_status`
- `analysis_id`
- `analysis_version`

## Provenance

Every derived result must be traceable through:

`run → dataset → file/sample → analysis version → inputs → result`

## Cross-modal linkage

A link between modalities is valid only when an explicit relationship exists, for example:

- shared subject + timepoint,
- shared specimen/sample ID,
- explicit anatomical mapping,
- explicit spatial coordinate/region mapping.

Dataset names, filenames and folder names are not sufficient evidence for a biological link.

## Interpretation boundary

The contract intentionally keeps these dimensions separate:

- disease-related evidence,
- ageing-related evidence,
- reference/normal evidence,
- uncertainty,
- missing evidence,
- need for deeper analysis.

A single universal health score is not the primary research representation.
