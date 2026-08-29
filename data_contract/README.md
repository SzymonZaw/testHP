# User Data Contract

This contract defines the **data supplied by a real user/study participant** to build a digital-twin observation set.

Public datasets are **not** user input. They are reference, training, calibration, or validation resources and are mapped separately in `dataset_mapping.yaml`.

## Minimum viable upload

A submission must contain:

- `subject_id`
- at least one `timepoint`
- acquisition time/date for each timepoint
- chronological age for biological-age interpretation
- at least one hand observation
- hand side (`left` or `right`)
- image metadata describing the view when an image is supplied

The minimum contract creates a macro-level twin. Deeper levels are optional and are only evaluated when corresponding evidence is present.

## Biological levels

- `macro`: hand photographs, video, 3D hand scans, landmarks
- `tissue`: histology/WSI and tissue regions
- `cellular`: microscopy, segmentation, single-cell data
- `molecular`: transcriptomics, spatial transcriptomics, genomics, proteomics

## Evidence policy

The pipeline must distinguish:

1. observed evidence,
2. missing evidence,
3. derived measurements,
4. model predictions,
5. uncertainty.

Missing molecular or cellular evidence must never be interpreted as evidence of a healthy state.

## Supported user file formats

The canonical contract uses references to uploaded files. Recommended formats:

- images: JPG, JPEG, PNG, TIFF
- video: MP4, MOV
- 3D: PLY, OBJ, GLB
- WSI/microscopy: TIFF, OME-TIFF, SVS
- single-cell: H5AD or Matrix Market (`matrix.mtx[.gz]`, `barcodes.tsv[.gz]`, `features.tsv[.gz]`) plus metadata
- spatial: expression matrix + coordinates + tissue image + metadata
- tabular metadata: CSV/TSV/JSON

## Submission shape

```text
submission/
├── metadata.json
└── T0/
    ├── hand/
    │   ├── left/
    │   │   ├── dorsal.jpg
    │   │   ├── palmar.jpg
    │   │   └── metadata.json
    │   └── right/
    ├── tissue/
    ├── cellular/
    └── molecular/
```

The same structure can be repeated for `T1`, `T2`, etc. Longitudinal analysis is optional but uses the same contract.

## Validation principle

Validation happens before model inference. A valid submission is allowed to be **partial**: the system reports which biological levels can actually be assessed rather than requiring every modality.
