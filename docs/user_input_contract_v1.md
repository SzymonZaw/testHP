# User Input Contract v1

The production input is a **declared package**, not a scan of `data/raw` and not a database record. A user may provide only the modalities they actually possess. Missing modalities stay missing; the system must not fabricate them.

## Package layout

```text
user_package/
├── manifest.json
└── data/
    ├── hand_images/
    ├── hand_video/
    ├── hand_3d/
    ├── tissue_wsi/
    ├── microscopy/
    ├── single_cell_rna/
    ├── bulk_rna/
    ├── genomics/
    ├── proteomics/
    ├── epigenetics/
    ├── clinical_context/
    └── ground_truth/
```

`manifest.json` is the authoritative description of every supplied artifact. Its JSON Schema is `configs/user_input_contract_v1.json`.

## Common metadata for every artifact

Each `inputs[]` item contains:

- `input_id` — stable identifier inside the package.
- `kind` — one of the supported modalities.
- `uri` — package-relative path such as `data/hand_images/front.jpg`.
- `format` — explicit file/data format (`jpeg`, `svs`, `h5ad`, `vcf`, `mzml`, `idat`, etc.).
- `provenance.source_type` — `user`, `clinical`, `research_dataset`, or `derived`.
- optional SHA-256 checksum, license/source ID, quality and modality metadata.

## What the user should normally supply

### A. Hand surface / 3D

Minimum useful package: left/right hand photographs with controlled acquisition metadata. Preferred views are `front`, `back`, `thumb`, `side_left`, `side_right`; include a scale reference when metric measurements are required. 3D is optional but preferred for geometry reconstruction when available.

Required acquisition metadata should eventually include camera/device, resolution, orientation, laterality, scale/marker status, lighting/calibration status and capture protocol version.

### B. WSI / histology

Preferred input is an original WSI in a supported pathology format plus slide metadata. The downstream chain is:

`WSI → tissue detection → cell/nucleus segmentation → cell type → cell coordinates → neighbourhood/microenvironment → tissue region → hand anatomical region`.

A WSI alone is **observed image evidence**. Cell health/disease and age are downstream model outputs unless an explicit reference label is supplied.

### C. Microscopy

Use for high-resolution fields, isolated cells or tissue microscopy. The package should preserve pixel size, magnification/objective, staining/channel information and specimen/region identifiers whenever available.

### D. Single-cell RNA / bulk RNA

Accepted examples include `h5ad`, Matrix Market (`mtx` plus barcodes/features), count tables and documented expression matrices. Preserve genome/reference build, gene identifiers, sample/cell identifiers and preprocessing status.

The system should transform expression into derived biological features rather than treating a raw expression file as a health label.

### E. Genomics

Preferred input is a standards-based variant representation such as VCF/BCF or a documented genotype matrix. Required metadata for interpretation includes genome assembly/reference build and sample identifier. Variant interpretation must remain provenance-aware.

### F. Proteomics

Preferred input is a documented protein/peptide abundance table or standard mass-spectrometry result with sample identifiers and processing information. Preserve protein identifiers, units and normalization state.

### G. Epigenetics

Accepted inputs can include methylation arrays/raw intensity data, beta-value matrices, or other documented chromatin/epigenetic measurements. Preserve assay type, probe/feature identifiers, genome build when applicable, sample ID and normalization state.

### H. Clinical context

Optional structured context such as age/date of birth, relevant diagnoses, medications, smoking/exposure history, and other variables that are legally and scientifically appropriate. Do not require sensitive clinical fields merely to run the imaging pipeline.

### I. Ground truth

Ground truth is separate evidence. It should identify the target object (cell/tissue/region/hand), label type, label value, source and assessment method. A model prediction must never be silently promoted to ground truth.

## Evidence semantics

Every result should distinguish:

- `observed` — directly measured/supplied data;
- `derived` — deterministic or analytical features derived from supplied data;
- `predicted` — model output;
- `ground_truth` — independently established reference label;
- `unavailable` — required evidence was not supplied.

## Important scientific boundary

This contract makes the software capable of accepting real multimodal data. It does **not** claim that a validated biological-age model, cell health classifier, disease classifier, or intervention recommendation already exists. Those require separately validated models and reference cohorts.
