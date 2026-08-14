from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

app = FastAPI(title="Human Pathology Platform", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _scan_directory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "files": 0, "bytes": 0, "children": []}
    files = [p for p in path.rglob("*") if p.is_file()]
    children = []
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if child.is_dir():
            info = _scan_directory(child)
            children.append({"name": child.name, "type": "directory", **info})
    return {
        "exists": True,
        "files": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "children": children,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status")
def status() -> dict[str, Any]:
    return {"status": "ready", "raw_data": RAW_DIR.exists(), "raw_path": str(RAW_DIR)}


@app.get("/api/datasets")
def datasets() -> dict[str, Any]:
    """Discover the actual contents of data/raw instead of requiring a fixed dataset list."""
    if not RAW_DIR.exists():
        return {"raw_exists": False, "datasets": []}
    result = []
    for category in sorted(RAW_DIR.iterdir(), key=lambda p: p.name.lower()):
        if category.is_dir():
            result.append({"name": category.name, **_scan_directory(category)})
    return {"raw_exists": True, "datasets": result}
