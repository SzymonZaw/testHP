from core.capability_report import Artifact, assess_capabilities, build_capability_report


def capability(report, level):
    return next(item for item in report["capabilities"] if item["level"] == level)


def test_photo_enables_only_macro_baseline():
    report = build_capability_report([Artifact("jpg", "hand/front.jpg")])

    assert capability(report, "macro")["available"] is True
    assert capability(report, "tissue")["available"] is False
    assert capability(report, "cellular")["available"] is False
    assert capability(report, "molecular")["available"] is False
    assert report["policy"]["missing_data_is_not_normal"] is True


def test_video_and_image_enable_enhanced_macro():
    report = build_capability_report(
        [Artifact("jpg", "hand/front.jpg"), Artifact("mp4", "hand/motion.mp4")]
    )

    assert capability(report, "macro")["available"] is True
    assert capability(report, "macro_enhanced")["available"] is True


def test_single_cell_assay_enables_cellular_and_molecular():
    report = build_capability_report([Artifact("h5ad", "sample.h5ad")])

    assert capability(report, "cellular")["available"] is True
    assert capability(report, "molecular")["available"] is True


def test_tissue_image_does_not_claim_cellular_or_molecular_results():
    capabilities = assess_capabilities([Artifact("svs", "biopsy.svs")])
    by_level = {item.level: item.available for item in capabilities}

    assert by_level["tissue"] is True
    assert by_level["cellular"] is False
    assert by_level["molecular"] is False
