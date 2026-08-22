from backend.spatial_provenance import lifecycle_transition


def test_lifecycle_is_monotonic_for_happy_path():
    path = ["created", "prepared", "registered", "reconstructed", "published"]
    assert all(lifecycle_transition(a, b) for a, b in zip(path, path[1:]))


def test_failed_result_can_reenter_preparation_or_registration():
    assert lifecycle_transition("failed", "prepared")
    assert lifecycle_transition("failed", "registered")


def test_invalid_lifecycle_transition_is_rejected():
    assert not lifecycle_transition("created", "published")
    assert not lifecycle_transition("prepared", "published")


def test_canonical_view_names_are_stable():
    from backend.hand_surface import SUPPORTED_VIEWS

    assert tuple(SUPPORTED_VIEWS) == (
        "front", "back", "side_left", "side_right", "thumb", "unknown"
    )


def test_spatial_object_contract_exposes_single_identity():
    from backend.spatial_contract import SpatialObject

    fields = set(getattr(SpatialObject, "__annotations__", {}))
    assert "spatial_object_id" in fields
    assert "coordinate_system" in fields
    assert "provenance" in fields
