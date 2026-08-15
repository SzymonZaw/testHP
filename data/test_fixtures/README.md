# Synthetic multimodal test fixtures

These files are **synthetic test inputs**, not biological measurements and not data from the project owner.

They are intentionally kept outside `data/raw/` so the production-style multiscale runner cannot accidentally treat them as evidence for `own_cohort`.

## What is included

- `hand/subject-TEST/session-001/T0/metadata.json` — explicit hand/session/timepoint metadata.
- `hand/subject-TEST/session-001/T1/metadata.json` — second timepoint metadata for longitudinal-contract tests.
- `rna/expression_demo.tsv` — tiny synthetic expression-like numeric matrix.
- `rna/sample_metadata_demo.tsv` — matching synthetic sample metadata.
- `wsi/wsi_demo_metadata.txt` — synthetic WSI/DICOM metadata example.

## Real files still required manually

The repository should eventually receive real, clearly provenance-labelled inputs for:

1. personal hand photographs at T0 and T1;
2. one or more valid hand videos;
3. independent normal/ageing/lesion skin images;
4. at least one real WSI/DICOM slide suitable for tile/cell analysis;
5. real RNA expression data with sample metadata.

Do not put synthetic fixture values into `data/raw/` and do not interpret them as health evidence.