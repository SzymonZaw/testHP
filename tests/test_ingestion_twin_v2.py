from backend.data_ingestion import allowed_extensions, destination_for
from backend.hand_twin_v2 import build_twin


def test_ingestion_extensions_cover_modalities():
    assert ".jpg" in allowed_extensions("hand")
    assert ".mp4" in allowed_extensions("video")
    assert ".svs" in allowed_extensions("wsi")
    assert ".csv" in allowed_extensions("rna")


def test_hand_destination_is_timepoint_aware():
    path = destination_for("hand", "own_cohort", "T1", None, "front", "front.jpg")
    assert path.as_posix().endswith("data/raw/hand/own_cohort/T1/front.jpg")


def test_twin_contains_nested_hand_zones():
    ontology = {
        "hand": [
            {"id": "thumb", "name": "Thumb", "children": ["distal", "nail"]},
            {"id": "palm", "name": "Palm", "children": ["thenar"]},
        ]
    }
    twin = build_twin("own_cohort", ontology)
    hand = twin.hands["hand-1"]
    assert "thumb" in hand.zones
    assert "thumb.distal" in hand.zones
    assert hand.zones["thumb.distal"].parent_id == "thumb"
    assert "palm.thenar" in hand.zones
