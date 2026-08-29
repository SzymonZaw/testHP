from data_contract.user_analysis_v1 import build_user_analysis_report, format_user_summary


def test_images_only_enables_macro_analysis():
    package = {"inputs": [{"input_id": "img-1", "kind": "hand_images"}]}
    report = build_user_analysis_report(package)
    ids = {x["capability_id"] for x in report["available_analyses"]}
    assert "macro_hand_analysis" in ids
    assert "single_cell_transcriptomic_analysis" not in ids
    assert report["safety"]["missing_data_is_not_negative_finding"] is True


def test_molecular_modalities_are_not_fabricated():
    package = {"inputs": [
        {"input_id": "rna-1", "kind": "single_cell_rna"},
        {"input_id": "geno-1", "kind": "genomics"},
    ]}
    report = build_user_analysis_report(package)
    ids = {x["capability_id"] for x in report["partial_analyses"]}
    assert "multimodal_molecular_state" in ids
    assert not any(x["capability_id"] == "proteomic_state_analysis" for x in report["available_analyses"])
    assert not any(x["capability_id"] == "epigenetic_state_analysis" for x in report["available_analyses"])


def test_summary_is_user_readable():
    package = {"inputs": [{"input_id": "img-1", "kind": "hand_images"}]}
    summary = format_user_summary(build_user_analysis_report(package))
    assert "AVAILABLE ANALYSES" in summary
    assert "macro_hand_analysis" in summary
    assert "LIMITATIONS" in summary
