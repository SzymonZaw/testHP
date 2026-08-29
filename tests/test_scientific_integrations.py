from integrations.model_registry import MODEL_REGISTRY, get_model_spec
from integrations.reference_data import alphafold_db_url, arc_virtual_cell_atlas_descriptor, cellxgene_census_query
from integrations.foundation_models import geneformer_handle, scgpt_handle, scgpt_spatial_handle, u_segment3d_handle, uni2_handle


def test_requested_integrations_are_registered():
    expected = {
        "hca", "cellxgene", "cellpose-sam", "uni2", "scgpt",
        "geneformer", "scgpt-spatial", "arc-virtual-cell-atlas",
        "u-segment3d", "alphafold-db",
    }
    assert expected <= MODEL_REGISTRY.keys()
    for integration_id in expected:
        assert get_model_spec(integration_id).source_url.startswith("https://")


def test_model_handles_are_lazy_and_serializable():
    assert scgpt_handle(model_version="test").integration_id == "scgpt"
    assert geneformer_handle().integration_id == "geneformer"
    assert scgpt_spatial_handle().integration_id == "scgpt-spatial"
    assert uni2_handle().integration_id == "uni2"
    assert u_segment3d_handle().integration_id == "u-segment3d"


def test_reference_descriptors():
    query = cellxgene_census_query(tissue="skin")
    assert "Homo sapiens" in query["query"]
    assert "skin" in query["query"]
    assert arc_virtual_cell_atlas_descriptor()["source"] == "arc-virtual-cell-atlas"
    assert alphafold_db_url("P04637").endswith("/P04637")
