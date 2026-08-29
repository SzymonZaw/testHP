from backend.anatomy_foundation import MultiscaleHierarchy
from backend.digital_twin_contract import DigitalTwin


def test_digital_twin_validates_identity_and_hierarchy():
    twin = DigitalTwin("t1", "subject-1", "hand-1", ("tp-1",), MultiscaleHierarchy("hand-1"))
    twin.validate()
    assert twin.snapshot("tp-1")["hand_id"] == "hand-1"


def test_digital_twin_rejects_unknown_timepoint():
    twin = DigitalTwin("t1", "subject-1", "hand-1", ("tp-1",))
    try:
        twin.snapshot("tp-2")
    except ValueError as exc:
        assert "unknown timepoint" in str(exc)
    else:
        raise AssertionError("expected ValueError")
