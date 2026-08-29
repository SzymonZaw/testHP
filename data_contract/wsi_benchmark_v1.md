# WSI benchmark protocol v1

## Purpose

This benchmark evaluates the existing WSI cell/nuclei pipeline against public annotated histology datasets. It is a technical benchmark, not evidence that the system is clinically validated for human hand or skin.

## Reference datasets

- **MoNuSAC 2020**: H&E images with expert annotations, 4 organs and four scored nucleus classes (epithelial, lymphocyte, macrophage, neutrophil). The official challenge metric uses weighted class-specific Panoptic Quality (PQ). The released data are CC BY-NC-SA 4.0. See the official data and metric pages.
- **PanNuke**: H&E nuclei instance segmentation/classification across 19 tissue types and five nuclei categories. It is suitable for broad technical benchmarking, not as hand-specific ground truth.

## Metrics

1. Instance detection: TP/FP/FN at IoU >= 0.50, precision, recall, F1, mean matched IoU.
2. Classification: accuracy and macro-F1 on matched nuclei only, plus per-class TP/FP/FN.
3. Official challenge metrics (for comparison where compatible) must be reported separately from this project's generic metrics.

## Evaluation rules

- Never tune thresholds on the held-out evaluation split.
- Preserve dataset split and patient/donor identity.
- Respect ambiguous/don't-care regions supplied by the dataset.
- Record dataset, version, preprocessing, model ID/version, threshold, and code revision.
- Do not map benchmark labels silently into the project's skin ontology.
- A benchmark pass does not enable end-user claims about disease, biological age, or hand-specific cell type.

## Current implementation

`pipeline/wsi_benchmark.py` provides reusable instance matching and generic detection/classification metrics. It does not download benchmark data and does not bundle datasets into the repository.

The next execution step is to build dataset adapters that convert the official MoNuSAC/PanNuke annotations into the benchmark interface, then run the held-out evaluation and store the resulting metrics as artifacts.
