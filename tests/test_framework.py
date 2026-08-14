from pathlib import Path

from framework.data import discover_raw
from framework.pipeline import FrameworkRunner


def test_framework_discovers_raw_tree(tmp_path: Path) -> None:
    (tmp_path / "data/raw/images/example").mkdir(parents=True)
    (tmp_path / "data/raw/images/example/a.jpg").write_bytes(b"fixture")
    statuses = discover_raw(tmp_path)
    example = next(item for item in statuses if item.name == "example")
    assert example.ready
    assert example.files == 1


def test_twin_smoke_contract() -> None:
    result = FrameworkRunner(Path(".")).twin_smoke()
    assert result["passed"] is True
    assert result["snapshot_count"] == 1
