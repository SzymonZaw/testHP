from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_merfish_local_preview.py"


def test_preview_builder_does_not_import_scanpy():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "import scanpy" not in source
    assert "import anndata as ad" in source


def test_preview_builder_uses_backed_anndata_read():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "ad.read_h5ad(input_path, backed=\"r\")" in source
    assert "without copying the expression matrix" in source
