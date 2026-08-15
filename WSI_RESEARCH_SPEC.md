# WSI modality — research specification

## Scope

`data/raw/wsi/` represents the **tissue/histology level**. It should answer questions that ordinary skin photographs cannot answer because it observes tissue architecture and cellular organization at much higher resolution.

The current run shows `TCGA-SKCM` as the usable WSI source, while several other WSI directories are currently empty or metadata-only. Those unavailable sources must remain visible as limitations.

## Scientific questions

The WSI layer should progressively determine:

1. Is a slide/file genuinely present and readable?
2. What specimen/section and acquisition metadata are available?
3. What tissue is represented and where?
4. What measurable tissue architecture and cellular morphology are present?
5. Which regions are unusual or require closer inspection?
6. Can a selected region be linked to an image-level ROI or molecular sample through explicit provenance?
7. What disease-related or ageing-related interpretation is supported by a validated analysis?

## Information map

| Level | Information | Result type |
|---|---|---|
| Input | slide existence, format, size, metadata | observation |
| Acquisition | pixel spacing, dimensions, magnification, stain/scan metadata | observation |
| Tissue | tissue area, architecture, compartment distribution | measurement/feature |
| Cellular | density, morphology, spatial arrangement | measurement/feature |
| ROI | candidate pathological/ageing region | feature/hypothesis |
| Molecular link | sample/specimen relationship to RNA or other data | explicit relationship |
| Interpretation | pathology/ageing state | validated interpretation only |

## Current data boundary

The current dashboard's DICOM reader intentionally reads metadata without loading pixel data. Therefore current WSI output such as file counts, matrix dimensions or metadata is **input characterization**, not histopathological interpretation.

## Analysis ladder

```text
W0  slide/input audit
 ↓
W1  metadata + acquisition quality
 ↓
W2  tissue detection / background removal
 ↓
W3  tissue architecture measurements
 ↓
W4  cellular segmentation + morphology
 ↓
W5  spatial organization / compartment analysis
 ↓
W6  candidate ROI detection
 ↓
W7  cross-link selected ROI to sample/specimen metadata
 ↓
W8  integrate molecular evidence where explicitly linked
 ↓
W9  validated pathology/ageing interpretation
```

## Important design rule

A WSI result must carry specimen/section identity and spatial coordinates. A tissue ROI cannot be connected to a hand photograph or RNA dataset simply because the datasets have similar names or describe the same disease.

## Desired final result

For each analyzed slide:

- specimen identity,
- acquisition metadata,
- usable tissue coverage,
- measured tissue features,
- cellular measurements,
- candidate ROIs,
- spatial coordinates,
- uncertainty/quality,
- linked evidence if an explicit sample relationship exists,
- validated interpretation if available,
- provenance.

## Completion criterion

The WSI phase is ready for integration when a selected tissue ROI can be represented reproducibly, measured at tissue/cellular level, and linked to another modality only through explicit specimen/sample/spatial provenance.
