from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from analysis.advanced_anomaly import AdvancedAnomalyDetector, AnomalyEvidence
from analysis.longitudinal import LongitudinalAnalyzer, LongitudinalPoint
from core.hierarchy import BiologicalNode, build_hierarchy
from datasets.dataset_registry import create_default_registry
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset
from evaluation.pipeline_evaluator import evaluate_pipeline
from decision.pipeline_decision import make_pipeline_decision
from audit.pipeline_audit import build_audit_record
from integration.observation_to_twin import ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def _quality_summary(observations: list[Any]) -> dict[str, Any]:
    scores = [float(item.quality_score) for item in observations]
    accepted = [score for score in scores if score >= 0.5]
    return {"observations": len(scores), "accepted": len(accepted), "rejected": len(scores) - len(accepted), "mean_quality": sum(scores) / len(scores) if scores else 0.0, "minimum_quality": min(scores) if scores else None}


def _build_hierarchy(observations: list[Any]) -> dict[str, Any]:
    nodes = [BiologicalNode("organism", "organism", "Research organism")]
    modalities = sorted({item.modality for item in observations if item.modality})
    for modality in modalities:
        system_id = f"system:{modality}"
        nodes.append(BiologicalNode(system_id, "system", modality, "organism"))
        nodes.append(BiologicalNode(f"site:{modality}", "site", "dataset observations", system_id))
    hierarchy = build_hierarchy(nodes)
    return {"nodes": len(hierarchy.nodes), "levels": {level: len(hierarchy.nodes_at_level(level)) for level in ("organism", "system", "organ", "tissue", "cell_population", "cell", "site")}, "paths": {node_id: hierarchy.path(node_id) for node_id in hierarchy.nodes}}


def _anomaly_and_longitudinal(observations: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = [AnomalyEvidence(item.feature, float(item.value), float(item.value), 1.0, float(item.quality_score), item.modality) for item in observations]
    anomaly_results = AdvancedAnomalyDetector(minimum_quality=0.5).assess(evidence)
    anomaly = {"results": [result.__dict__ for result in anomaly_results], "insufficient_evidence": any(result.insufficient_evidence for result in anomaly_results) or not observations, "note": "No abnormality is inferred from a single ingestion run; reference/baseline evidence is required."}
    grouped: dict[str, list[LongitudinalPoint]] = {}
    for item in observations:
        grouped.setdefault(item.feature, []).append(LongitudinalPoint("web-run-1", 1.0, float(item.value), float(item.quality_score)))
    analyzer = LongitudinalAnalyzer(minimum_quality=0.5, minimum_points=2)
    trends = [analyzer.analyze(feature, points) for feature, points in grouped.items()]
    return anomaly, {"features": len(trends), "trends": [result.__dict__ for result in trends], "insufficient_evidence": True, "note": "At least two independent timepoints are required before a trajectory is reported."}


def run_datasets(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Run the real data pipeline and report limitations instead of masking them.

    An empty dataset selection is a valid execution/diagnostic run, but it is not
    reported as successful analysis. No biological observations are fabricated.
    Explicitly requested datasets remain strict and report missing/invalid sources
    as ``blocked``.
    """
    registry = create_default_registry()
    available = {item.name: item for item in registry.all()}
    explicit_selection = bool(dataset_names)

    if explicit_selection:
        selected = list(dataset_names or [])
        missing = [name for name in selected if name not in available]
        invalid = [name for name in selected if name in available and not available[name].has_data()]
        datasets = [available[name] for name in selected if name in available and available[name].has_data()]
    else:
        datasets = [item for item in available.values() if item.has_data()]
        selected = sorted(item.name for item in datasets)
        missing = []
        invalid = []

    if missing or invalid:
        return {"status": "blocked", "selected": selected, "missing": missing, "invalid": invalid, "datasets": [], "stages": [], "fusion": None, "snapshot": None}

    normalized = {item.name: normalize_dataset(item) for item in datasets}
    invalid_normalized = [name for name, item in normalized.items() if not item.valid]
    if invalid_normalized and explicit_selection:
        return {"status": "blocked", "selected": selected, "missing": [], "invalid": invalid_normalized, "datasets": [], "stages": [], "fusion": None, "snapshot": None}
    normalized = {name: item for name, item in normalized.items() if item.valid}

    fusion = fuse(normalized.values())
    observations = [observation for item in normalized.values() for observation in item.observations]
    observations.extend(fusion.observations)
    quality = _quality_summary(observations)
    hierarchy = _build_hierarchy(observations)

    twin = DigitalBiologicalTwin(subject_id="web-demo")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
    snapshot = pipeline.ingest("web-run-1", observations, datetime.now(timezone.utc))
    anomaly, longitudinal = _anomaly_and_longitudinal(observations)

    evaluation = evaluate_pipeline(observations=observations, modalities=list(fusion.modalities), warnings=list(fusion.warnings)).to_dict()
    decision = make_pipeline_decision(evaluation=evaluation, quality=float(quality["mean_quality"]), temporal_values=None)

    has_observations = bool(observations)
    analytical_status = "completed" if has_observations else "insufficient_data"
    overall_status = "completed" if has_observations else "insufficient_data"
    limitation = None if has_observations else "No biological observations were available; execution was completed, but analytical conclusions cannot be made."

    result = {
        "status": overall_status,
        "selected": selected,
        "missing": [],
        "invalid": [],
        "limitations": [limitation] if limitation else [],
        "stages": [
            {"stage": 1, "name": "ingestion_validation", "status": "completed"},
            {"stage": 2, "name": "normalization_preprocessing", "status": "completed"},
            {"stage": 3, "name": "multimodal_fusion", "status": "completed"},
            {"stage": 4, "name": "quality_uncertainty", "status": analytical_status, "summary": quality, "reason": limitation},
            {"stage": 5, "name": "hierarchical_biological_state", "status": analytical_status, "summary": hierarchy, "reason": limitation},
            {"stage": 6, "name": "digital_biological_twin", "status": analytical_status, "summary": {"subject_id": twin.subject_id, "snapshots": len(twin.history())}, "reason": limitation},
            {"stage": 7, "name": "anomaly_longitudinal_analysis", "status": "completed" if has_observations else "insufficient_data", "anomaly": anomaly, "longitudinal": longitudinal, "reason": longitudinal["note"]},
            {"stage": 8, "name": "pipeline_evaluation", "status": analytical_status, "summary": evaluation, "reason": limitation},
            {"stage": 9, "name": "decision_support", "status": analytical_status, "summary": decision, "reason": limitation},
        ],
        "datasets": [{"name": item.dataset, "path": item.source_path, "modality": item.modality, "files": item.files, "bytes": item.bytes, "observations": len(item.observations), "warnings": list(item.warnings), "status": "ok"} for item in normalized.values()],
        "fusion": {"datasets": list(fusion.datasets), "modalities": list(fusion.modalities), "linked_subjects": fusion.linked_subjects, "warnings": list(fusion.warnings), "observation_count": len(fusion.observations)},
        "snapshot": {"timepoint_id": snapshot.timepoint_id, "captured_at": snapshot.captured_at.isoformat(), "observation_count": len(snapshot.state), "provenance": list(snapshot.provenance), "state": snapshot.state},
    }
    audit = build_audit_record(run_id="web-run-1", result=result)
    result["stages"].append({"stage": 10, "name": "audit_and_provenance", "status": "completed", "summary": {"run_id": audit["run_id"], "created_at": audit["created_at"], "limitations": audit["limitations"]}})
    result["audit"] = audit
    return result
