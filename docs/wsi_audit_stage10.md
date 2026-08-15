# WSI modality audit — Stage 10

## Role

`data/raw/wsi/` is the tissue/histology layer. Its purpose is to move the platform below ordinary macroscopic imagery toward tissue architecture and, eventually, cell-level evidence.

It is fundamentally different from `images/`: ordinary skin photographs describe visible surface/macroscopic appearance, while WSI/pathology data can expose microscopic tissue organization. A WSI result must therefore not be substituted for a macroscopic image result and vice versa.

## Current repository structure

The current WSI tree contains four conceptual groups:

- `aging/`
- `bcc/`
- `melanoma/`
- `normal/`

Only the melanoma branch currently contains a populated TCGA-SKCM example in the repository tree. The other groups currently need data-availability verification before being treated as active evidence sources.

## Current populated source: TCGA-SKCM

`data/raw/wsi/melanoma/TCGA-SKCM/` contains an IDC manifest, an `info.txt`, and a nested `tcga_skcm/` directory. That directory currently contains three DICOM files. The files are small repository test/sample objects rather than full clinical-scale WSI assets.

The immediate implication is that the current WSI layer is useful for validating DICOM discovery and metadata extraction, but it is **not yet evidence that the platform can perform full whole-slide pathology analysis**.

## Information map

### Acquisition / technical level

- file existence and readability;
- DICOM validity;
- SOP/series identifiers;
- dimensions and matrix information;
- pixel representation and transfer syntax;
- pathology/slide metadata;
- magnification or resolution metadata when present;
- source dataset and manifest provenance.

### Tissue level

When true slide-resolution data are available:

- tissue/background separation;
- tissue area and coverage;
- tissue compartments;
- architectural organization;
- staining/colour descriptors;
- nuclei/cell density;
- morphology and spatial organization;
- candidate regions of interest.

### Cellular level

After validated cell/nuclei segmentation:

- cell/nucleus counts;
- size and shape distributions;
- nuclear morphology;
- spatial density and neighbourhood structure;
- validated pathological or ageing-related markers when the assay actually measures them.

### Spatial linkage

A WSI observation can be attached to the digital twin only when an explicit relationship exists between the tissue sample and the investigated subject/region. A public TCGA sample cannot be silently attached to the user's hand.

## Interpretation boundary

WSI data can support much stronger biological interpretation than ordinary RGB photographs, but the platform must still distinguish:

1. measured tissue/cellular morphology;
2. validated derived features;
3. pathology/ageing interpretation supported by a validated model or assay.

The presence of a folder called `melanoma` or `bcc` is dataset provenance, not a diagnosis of a future sample.

## Engineering ladder for WSI

1. DICOM/file validation.
2. Metadata extraction.
3. Pixel/tile availability detection.
4. Slide/tissue segmentation.
5. Tiling and multiscale pyramid access.
6. Tissue compartment analysis.
7. Cell/nuclei segmentation.
8. Cell morphology and spatial features.
9. Validated pathology/ageing models.
10. Spatial linkage to a subject/region.
11. Multimodal integration with macro images and molecular evidence.

## Stage 10 decision

`wsi/` is frozen as the **tissue and microscopic evidence layer**. Its near-term implementation should focus on robust DICOM metadata/tile handling and tissue/cell measurements. Biological conclusions remain a later validated stage.
