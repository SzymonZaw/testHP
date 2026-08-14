from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from analysis.advanced_anomaly import AdvancedAnomalyDetector, AnomalyEvidence
from analysis.longitudinal import LongitudinalAnalyzer, LongitudinalPoint
from core.hierarchy import BiologicalNode, build_hierarchy
from datasets.dataset_registry import create_default_registry
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset
from integration.observation_to_twin import ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def _quality_summary(observations: list[Any]) -> dict[str, Any]:
    scores = [float(item.quality_score) for item in observations]
    accepted = [score for score in scores if score >= 0.5]
    return {
        "observations": len(scores),
        "accepted": len(accepted),
        "rejected": len(scores) - len(accepted),
        "mean_quality": sum(scores) / len(scores) if scores else 0.0,
        "minimum_quality": min(scores) if scores else None,
    }


def _build_hierarchy(observations: list[Any]) -> dict[str, Any]:
    """Create a provenance-preserving biological hierarchy from available modalities.

    Public datasets generally do not share subject identifiers, so the hierarchy
    deliberately uses modality nodes instead of inventing cross-dataset subjects.
    """
    nodes = [BiologicalNode("organism", "organism", "Research organism")]
    modalities = sorted({item.modality for item in observations if item.modality})
    for modality in modalities:
        system_id = f"system:{modality}"
        nodes.append(BiologicalNode(system_id, "system", modality, "organism"))
        nodes.append(BiologicalNode(f"site:{modality}", "site", "dataset observations", system_id))
    hierarchy = build_hierarchy(nodes)
    return {
        "nodes": len(hierarchy.nodes),
        "levels": {level: len(hierarchy.nodes_at_level(level)) for level in ("organism", "system", "organ", "tissue", "cell_population", "cell", "site")},
        "paths": {node_id: hierarchy.path(node_id) for node_id in hierarchy.nodes},
    }


def _anomaly_and_longitudinal(observations: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run conservative stages 6-7; single-run data yields explicit insufficiency."""
    evidence = [
        AnomalyEvidence(item.feature, float(item.value), float(item.value), 1.0, float(item.quality_score), item.modality)
        for item in observations
    ]
    anomaly_results = AdvancedAnomalyDetector(minimum_quality=0.5).assess(evidence)
    anomaly = {
        "results": [result.__dict__ for result in anomaly_results],
        "insufficient_evidence": any(result.insufficient_evidence for result in anomaly_results),
        "note": "No abnormality is inferred from a single ingestion run; reference/baseline evidence is required.",
    }

    grouped: dict[str, list[LongitudinalPoint]] = {}
    for item in observations:
        grouped.setdefault(item.feature, []).append(
            LongitudinalPoint("web-run-1", 1.0, float(item.value), float(item.quality_score))
        )
    analyzer = LongitudinalAnalyzer(minimum_quality=0.5, minimum_points=2)
    trends = [analyzer.analyze(feature, points) for feature, points in grouped.items()]
    longitudinal = {
        "features": len(trends),
        "trends": [result.__dict__ for result in trends],
        "insufficient_evidence": True,
        "note": "At least two independent timepoints are required before a trajectory is reported.",
    }
    return anomaly, longitudinal


def run_datasets(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Execute stages 1-7 on the data actually available in data/raw."""
    registry = create_default_registry()
    available = {item.name: item for item in registry.all()}
    selected = dataset_names or sorted(available)
    missing = [name for name in selected if name not in available]
    datasets = [available[name] for name in selected if name in available]

    normalized = {item.name: normalize_dataset(item) for item in datasets}
    invalid = [name for name, item in normalized.items() if not item.valid]
    if missing or invalid:
        return {
            "status": "blocked",
            "selected": selected,
            "missing": missing,
            "invalid": invalid,
            "datasets": [],
            "stages": [],
            "fusion": None,
            "snapshot": None,
        }

    fusion = fuse(normalized.values())
    observations = [observation for item in normalized.values() for observation in item.observations]
    observations.extend(fusion.observations)

    # Stage 4: quality / uncertainty gate.
    quality = _quality_summary(observations)

    # Stage 5: hierarchical biological state.
    hierarchy = _build_hierarchy(observations)

    # Stage 6: digital biological twin snapshot.
    twin = DigitalBiologicalTwin(subject_id="web-demo")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
    snapshot = pipeline.ingest("web-run-1", observations, datetime.now(timezone.utc))

    # Stage 7: conservative temporal/anomaly analysis.
    anomaly, longitudinal = _anomaly_and_longitudinal(observations)

    return {
        "status": "completed",
        "selected": selected,
        "missing": [],
        "invalid": [],
        "stages": [
            {"stage": 1, "name": "ingestion_validation", "status": "completed"},
            {"stage": 2, "name": "normalization_preprocessing", "status": "completed"},
            {"stage": 3, "name": "multimodal_fusion", "status": "completed"},
            {"stage": 4, "name": "quality_uncertainty", "status": "completed", "summary": quality},
            {"stage": 5, "name": "hierarchical_biological_state", "status": "completed", "summary": hierarchy},
            {"stage": 6, "name": "digital_biological_twin", "status": "completed", "summary": {"subject_id": twin.subject_id, "snapshots": len(twin.history())}},
            {"stage": 7, "name": "anomaly_longitudinal_analysis", "status": "completed", "anomaly": anomaly, "longitudinal": longitudinal},
        ],
        "datasets": [
            {
                "name": item.dataset,
                "path": item.source_path,
                "modality": item.modality,
                "files": item.files,
                "bytes": item.bytes,
                "observations": len(item.observations),
                "warnings": list(item.warnings),
                "status": "ok",
            }
            for item in normalized.values()
        ],
        "fusion": {
            "datasets": list(fusion.datasets),
            "modalities": list(fusion.modalities),
            "linked_subjects": fusion.linked_subjects,
            "warnings": list(fusion.warnings),
            "observation_count": len(fusion.observations),
        },
        "snapshot": {
            "timepoint_id": snapshot.timepoint_id,
            "captured_at": snapshot.captured_at.isoformat(),
            "observation_count": len(snapshot.state),
            "provenance": list(snapshot.provenance),
            "state": snapshot.state,
        },
    }
