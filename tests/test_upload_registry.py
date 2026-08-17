from pathlib import Path

import pytest

from backend.data_ingestion import unique_destination


def test_unique_destination_versions_existing_file(tmp_path: Path):
    target = tmp_path / "T1" / "front.jpg"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"first")
    (target.parent / "front_v2.jpg").write_bytes(b"second")

    result = unique_destination(target)

    assert result.name == "front_v3.jpg"
    assert not result.exists()
