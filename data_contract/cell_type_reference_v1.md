# Cell-type reference contract v1

## Purpose

This contract defines the public reference resources that may be used to train, benchmark, or validate the end-user cell-type annotation layer. Reference data are **not** treated as patient input and must not be copied into `data/user_uploads/`.

## Recommended primary references

### 1. Human Skin Cell Atlas (HSCA)

- Scope: healthy human skin scRNA-seq reference, with harmonised cell-type nomenclature; the 2026 data release integrates 34 public healthy-skin datasets and ~820,000 cells.
- Best use: primary skin cell-type reference and label harmonisation.
- Data landing page: https://zenodo.org/records/21022952
- Code: https://github.com/TolgaDuz/HSCA
- DOI: 10.5281/zenodo.21022952
- Status in this project: `reference_candidate`, not yet bundled into the repository.

### 2. Tabula Sapiens

- Scope: multi-organ human single-cell reference including skin; cell types are annotated using a defined ontology and the dataset provides reference transcriptomes.
- Best use: cross-tissue reference, independent benchmark, and ontology cross-check.
- Publication/data portal: https://tabula-sapiens.sf.czbiohub.org/
- Publication: https://pmc.ncbi.nlm.nih.gov/articles/9812260/
- Status in this project: `reference_candidate`, not yet bundled into the repository.

### 3. Human Protein Atlas single-cell skin

- Scope: skin single-cell expression and cell-type marker information derived from Tabula Sapiens and HPA resources.
- Best use: marker-gene sanity checks and interpretable reference evidence.
- Landing page: https://www.proteinatlas.org/humanproteome/single-cell+type
- Status in this project: `secondary_reference`.

### 4. Tabula Sapiens skin popV model

- Scope: pretrained cell-type annotation model for Tabula Sapiens skin data.
- Best use: independent baseline for scRNA-seq cell-type annotation experiments.
- Model page: https://huggingface.co/popV/tabula_sapiens_Skin
- License shown by the model page: CC-BY-4.0.
- Status in this project: `external_model_candidate`; it must be evaluated on a held-out dataset before being exposed as an end-user model.

## Canonical project label groups

The project should initially expose conservative parent labels:

- `keratinocyte`
- `fibroblast`
- `endothelial`
- `pericyte_mural`
- `immune`
- `langerhans`
- `melanocyte`
- `smooth_muscle`
- `schwann_glial`
- `other`
- `unknown`

Fine-grained labels must retain the original source ontology term and an explicit mapping to one of these parent groups. No source label should be silently renamed.

## Ground-truth policy

A reference annotation is not automatically ground truth for a new user sample. Each benchmark record must retain:

- source dataset/study;
- donor/sample identifier;
- original cell-type label;
- mapped project label;
- annotation method;
- evidence/marker information when available;
- train/validation/test split;
- model identifier/version when a prediction is involved.

For end-user inference, the output must report the reference/model used, confidence, and whether the prediction is inside the validated domain.

## Important limitation

These resources solve the **reference-label problem**, not the complete WSI problem. A scRNA-seq reference cannot by itself validate morphology-only classification from an H&E/WSI image. The project therefore needs an image/spatial reference with cell-level annotations before a morphology-only WSI classifier can be considered validated.
