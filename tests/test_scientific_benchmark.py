from integrations.benchmark import BenchmarkResult, rank_models, select_best
from integrations.integration_catalog import get_integration, list_integrations


def test_additional_integrations_are_discoverable() -> None:
    assert get_integration("scfoundation").name == "scFoundation"
    assert get_integration("scvi-tools").name == "scvi-tools"
    assert get_integration("cellsam").name == "CellSAM"
    assert get_integration("nicheformer").name == "Nicheformer"
    assert get_integration("virtues").name == "VirTues / Virtual Tissues"


def test_catalog_can_filter_by_tag() -> None:
    segmentation = list_integrations(tag="segmentation")
    ids = {item.id for item in segmentation}
    assert {"cellpose-sam", "u-segment3d", "cellsam", "stardist"}.issubset(ids)


def test_benchmark_ranking_is_model_agnostic() -> None:
    results = [
        BenchmarkResult("model-a", "segmentation", {"dice": 0.91}, 0.91, 20),
        BenchmarkResult("model-b", "segmentation", {"dice": 0.95}, 0.95, 20),
        BenchmarkResult("model-c", "segmentation", {"dice": 0.88}, 0.88, 20),
    ]
    ranked = rank_models(results)
    assert [item.model_id for item in ranked] == ["model-b", "model-a", "model-c"]
    assert select_best(results).model_id == "model-b"
