# Raw data ingestion

`data/raw/` is the immutable source layer. Files are never moved, renamed, or modified by ingestion.

The current layout is intentionally preserved:

```text
data/raw/
├── hand/
│   ├── own_cohort/
│   ├── media/
│   └── InterHand2_6M/
├── images/
├── rna/
└── wsi/
```

Ingestion scans this tree and creates normalized metadata for downstream observation processing. It infers a conservative modality from the file extension and path, while retaining the original relative path as provenance.

The ingestion layer is deliberately tolerant of future multimodal content: images, video, WSI, RNA/tabular data and text can coexist under a domain without forcing the user to reorganize the raw files first.

## Contract

```text
raw file
  -> Artifact
  -> Observation (when sufficient metadata exists)
  -> Evidence
  -> analysis / Digital Twin
```

No step in this layer writes back into `data/raw/`.
