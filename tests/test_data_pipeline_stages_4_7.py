from backend.service import run_datasets


def test_stages_4_to_7_execute_without_inventing_evidence():
    result = run_datasets([])

    # The pipeline is allowed to execute without input data, but it must not
    # claim that an analytical result was completed. This is a valid diagnostic
    # state, not an error and not fabricated evidence.
    assert result["status"] == "insufficient_data"
    stages = {item["stage"]: item for item in result["stages"]}
    assert all(number in stages for number in (4, 5, 6, 7))
    assert stages[4]["status"] == "insufficient_data"
    assert stages[5]["status"] == "insufficient_data"
    assert stages[6]["status"] == "insufficient_data"
    assert stages[7]["status"] == "insufficient_data"
    assert stages[4]["summary"]["observations"] == 0
    assert stages[5]["summary"]["nodes"] >= 1
    assert stages[6]["summary"]["snapshots"] == 1
    assert stages[7]["longitudinal"]["insufficient_evidence"] is True


def test_stage_7_requires_multiple_timepoints():
    result = run_datasets([])
    longitudinal = result["stages"][6]["longitudinal"]
    assert longitudinal["insufficient_evidence"] is True
    assert "two independent timepoints" in longitudinal["note"]
