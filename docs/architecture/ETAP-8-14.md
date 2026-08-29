# ETAPY 8-14 — Biological assessment layer

These stages add validated domain contracts, not clinical-grade diagnostic models.

## 8. Cell Health

`CellHealthAssessment` represents Healthy, Altered, Stressed, Senescent, Damaged and Unknown. It stores baseline, deviations, stress/senescence/damage scores, morphology flags, biomarkers, confidence, evidence and expert-validation status. Unknown requires explicit limitations.

## 9. Biological Age

`BiologicalAgeAssessment` is cell-type-specific and stores reference dataset, biomarkers, model/version, calibration, independent validation status, estimate and uncertainty interval. The contract does not assume one universal cellular age.

## 10. Pathology

`PathologySignal` and `AbnormalityCluster` anchor abnormal signals to `spatial_id`, cells and tissues, with confidence, evidence, model version and expert validation status.

## 11. Temporal Twin

`TemporalTwin` stores timepoints, observations, changes, rates and evidence. Tracking is only asserted when the data supports it.

## 12. Personal Baseline

`PersonalBaseline` defines individual normal ranges and `BaselineDeviation` compares current measurements to the person's baseline first, with population comparison explicitly recorded.

## 13. Risk Map

`RiskMapEntry` supports normal/monitor/elevated/high/unknown levels, spatial aggregation metadata, evidence, rationale and confidence. The visualization layer can map these entries to the 3D twin.

## 14. Intervention Map

`InterventionMapEntry` supports observe/investigate/treat/regenerate/none. Treatment and regeneration require expert review. The system records limitations and evidence and must not turn a risk signal into an automatic treatment instruction.

## Data flow

```text
Cell observations
      ↓
Cell Health / Biological Age
      ↓
Pathology signals
      ↓
Temporal + Personal Baseline
      ↓
Risk Map
      ↓
Intervention Map
      ↓
Human / Expert review
```
