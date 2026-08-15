# Stages 6–10 status

## Completed in this pass

### Stage 6 — Observation vs interpretation

Completed by freezing three result classes:

- `observation` — directly measured from available evidence;
- `derived_feature` — deterministic/validated transformation without a biological cause claim;
- `interpretation` — biological statement requiring validated evidence.

The result envelope and hard inference boundaries are documented in `hand_evidence_contract_v1.md`.

### Stage 7 — Analysis ladder

Completed as a progressive ladder from input integrity through macro, spatial, tissue, cellular and molecular analysis, followed by multimodal and longitudinal interpretation.

The important rule is that deeper levels become **inactive/unavailable** when their evidence is absent; the system does not fabricate them.

### Stage 8 — Hand result definition

Completed as the first implementation contract for personal hand data:

- acquisition/quality;
- hand localization;
- landmarks;
- canonical coordinates;
- wrist/palm/five-digit regions;
- macroscopic descriptors;
- temporal features when video is available;
- explicit missing deeper evidence;
- future attachment points for tissue/cellular/molecular data.

### Stage 9 — Images audit

Completed for the current `data/raw/images/` structure.

Important findings:

1. `aging_skin/` currently contains three own photographs and metadata identifying them as own photographs.
2. `normal_skin/` currently contains three JPEGs with the same Git object SHAs as `aging_skin/`; therefore it cannot yet be treated as an independent normal reference set.
3. `lesions/` contains `ISIC` and `skin_lesions_dataset` reference sources.
4. `pathology/scin/` is scientifically ambiguous; the folder name alone does not establish histopathology. It should be treated as a skin-condition image source until verified.

The image information map and recommended output boundary are documented in `images_information_map.json` and `images_audit_stage9.md`.

### Stage 10 — WSI audit

Completed for the current `data/raw/wsi/` structure:

- `aging/`
- `bcc/`
- `melanoma/`
- `normal/`

The currently populated example is `melanoma/TCGA-SKCM`, with an IDC manifest, metadata and three DICOM files. This is enough to establish DICOM discovery/metadata handling, but it is not yet a full whole-slide pathology-analysis benchmark.

The WSI information map and implementation ladder are documented in `wsi_information_map.json` and `wsi_audit_stage10.md`.

## Scientific decisions frozen

The project now treats:

```text
hand   = multimodal fragment entry point
images = macroscopic skin observation
wsi    = tissue / microscopic evidence
rna    = molecular / transcriptomic evidence
```

These layers can eventually connect through explicit subject/sample/specimen/spatial identifiers, but filenames, dataset names and directory membership are never sufficient to create a biological relationship.

## What this enables next

The next step is no longer conceptual auditing of these two modalities. The next implementation work can start from the frozen contracts:

1. implement the hand macroscopic result contract;
2. repair/clarify the duplicated `normal_skin` test data;
3. implement the macroscopic image measurement contract;
4. implement robust WSI/DICOM metadata and tile handling;
5. then perform the equivalent scientific pass for `rna/` before multimodal integration.
