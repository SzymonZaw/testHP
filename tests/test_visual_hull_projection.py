from backend.visual_hull import build_visual_hull


def _record(view):
    return {
        "view": view,
        "status": "registered",
        "registration": {
            "status": "registered",
            "quality": 0.9,
            "transform": {"origin": [10, 20], "scale": 100},
            "landmarks": [
                {"x": 0.2, "y": 0.2, "z": 0},
                {"x": 0.8, "y": 0.2, "z": 0},
                {"x": 0.5, "y": 0.8, "z": 0},
                {"x": 0.5, "y": 0.5, "z": 0},
            ],
        },
    }


def test_projection_ready_mesh_has_uv_and_camera_contract():
    mesh = build_visual_hull([_record("front"), _record("back")], resolution=12)
    assert mesh["projection_ready"] is True
    assert mesh["physical_calibration"] is False
    assert mesh["calibration"] == "registration-derived-orthographic-v1"
    assert len(mesh["uv"]) == len(mesh["vertices"])
    assert {camera["view"] for camera in mesh["cameras"]} == {"front", "back"}
    assert all(0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 for u, v in mesh["uv"])
