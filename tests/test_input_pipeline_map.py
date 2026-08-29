from core.input_pipeline_map import routes_for_inputs, unmapped_inputs


def test_all_contract_modalities_have_a_route():
    expected = {
        "hand_images", "hand_video", "hand_3d", "tissue_wsi", "microscopy",
        "single_cell_rna", "molecular_assay", "genomics", "proteomics",
    }
    assert unmapped_inputs(expected) == []


def test_photo_routes_to_macro_modules():
    routes = routes_for_inputs({"hand_images"})
    assert len(routes) == 1
    assert routes[0].stage == "macro"
    assert "analysis.morphology_analysis" in routes[0].modules


def test_single_cell_routes_to_rna_and_cell_analysis():
    routes = routes_for_inputs({"single_cell_rna"})
    assert routes[0].stage == "cellular"
    assert "analysis.rna_analysis" in routes[0].modules
    assert "analysis.cell_analysis" in routes[0].modules


def test_proteomics_is_explicitly_unprocessed():
    routes = routes_for_inputs({"proteomics"})
    assert routes[0].modules == ()


def test_unknown_input_is_reported():
    assert unmapped_inputs({"future_modality"}) == ["future_modality"]
