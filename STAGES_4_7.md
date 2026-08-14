# Stages 4-7

The web pipeline now executes the next four stages after ingestion, normalization and multimodal fusion.

## Stage 4 — quality and uncertainty gate

All normalized observations carry a quality score. The pipeline reports accepted/rejected counts, mean quality and minimum quality. Observations below the configured threshold are not admitted into the digital-twin snapshot.

## Stage 5 — hierarchical biological state

A provenance-preserving hierarchy is built from the modalities actually present. Public datasets are not treated as if they belonged to the same person: modality/system/site nodes are used when no shared subject identifier exists.

## Stage 6 — digital biological twin

The accepted observations are ingested into `DigitalBiologicalTwin` as a timestamped `TwinSnapshot`. Provenance is retained. This is a computational state snapshot, not a predictive or clinical twin.

## Stage 7 — anomaly and longitudinal analysis

The anomaly and longitudinal modules execute on the available observations. With only one ingestion timepoint, the system deliberately returns `insufficient_evidence` for trajectory claims rather than fabricating a trend or abnormality. Two or more independent timepoints are required for a longitudinal trend.

The API endpoint `/api/run` returns the results and status of all stages 1–7.
