from backend.digital_twin_report import build_digital_twin_report


def test_report_contains_complete_multiscale_snapshot():
    report = build_digital_twin_report(
        subject_id="s1", hand_id="h1", timepoint_id="T1",
        anatomy=[{"structure_id": "skin"}],
        tissues=[{"tissue_id": "t1"}],
        cells=[{"cell_id": "c1"}],
        assessments=[{"cell_id": "c1", "state": "normal"}],
        biological_age=[{"cell_id": "c1", "age": 42.0}],
        trends=[{"zone": "c1", "delta": 1.0}],
        attention=[{"zone_id": "t1", "score": 0.4}],
        spatial_attention=[{"zone_id": "t1", "centroid": (1.0, 2.0, 3.0)}],
    )
    assert report["subject_id"] == "s1"
    assert report["hand_id"] == "h1"
    assert report["timepoint_id"] == "T1"
    assert report["cells"][0]["cell_id"] == "c1"
    assert report["biological_age"][0]["age"] == 42.0
    assert report["spatial_attention"][0]["centroid"] == (1.0, 2.0, 3.0)


def test_report_rejects_non_mapping_components():
    try:
        build_digital_twin_report(
            subject_id="s1", hand_id="h1", timepoint_id="T1",
            anatomy=["not-a-dict"], tissues=[], cells=[], assessments=[],
            biological_age=[], trends=[], attention=[], spatial_attention=[],
        )
    except TypeError:
        pass
    else:
        raise AssertionError("non-dict report component should be rejected")
