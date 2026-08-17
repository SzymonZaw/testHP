# Dataset management

The platform now distinguishes a **dataset** from the physical files found under `data/raw/`.

## Dataset identity

Every managed dataset has:

- stable `dataset_id`;
- name and modality;
- version;
- description and source/provenance;
- optional license and tags;
- a raw root directory;
- a machine-readable manifest;
- a lifecycle status (`draft` or `ready`).

The registry is stored locally in `data/registry/datasets.json`. Manifests are stored in `data/registry/manifests/`. These are metadata, not copies of the biological files.

## Existing data

Existing configured directories are registered automatically the first time the API sees them. Their files are **not moved or copied**. The generated dataset record points to the existing `data/raw/...` path.

This means the current repository data can gradually become first-class datasets without a destructive migration.

## Creating a dataset

From the frontend use **Dataset Management → Create dataset**. The API is:

```text
POST /api/datasets
```

Example payload:

```json
{
  "name": "own_hand_cohort_v1",
  "modality": "hand",
  "description": "Longitudinal own-cohort hand images",
  "source": "Own cohort",
  "version": "1.0",
  "tags": ["hand", "longitudinal"]
}
```

The platform creates a dataset directory such as:

```text
data/raw/hand/datasets/DS-XXXXXXXXXX/
```

and an empty manifest.

## Adding files

The frontend can upload directly into a managed dataset:

```text
POST /api/datasets/{dataset_id}/upload
```

The file is stored below the dataset root and the manifest is refreshed immediately.

Subject and timepoint metadata are directory metadata only; the platform does not infer identity from filenames.

## Manifest

```text
GET /api/datasets/{dataset_id}/manifest
```

The manifest records each physical file, its relative path, size and availability. It is the source of truth for which files belong to that dataset version.

## Research pipeline

The pipeline now includes managed datasets in its selection registry. A managed dataset therefore becomes an explicit pipeline input rather than an accidental consequence of scanning arbitrary files.

The existing raw inventory remains available because manually placed files are still important during the migration period.

## Scientific boundary

Dataset registration is not biological interpretation. A dataset can be `ready` because its files are present and structurally usable; that does not mean the contents are scientifically validated or clinically meaningful.

Likewise, public datasets are not linked to the personal cohort without explicit identifiers.
