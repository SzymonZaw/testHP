from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.pipeline import build_pipeline
from datasets.dataset_registry import create_default_registry

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

app = FastAPI(title="Human Pathology Platform", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PipelineRequest(BaseModel):
    datasets: list[str] = Field(default_factory=list)


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
    registry = create_default_registry()
    return {
        "status": "ready",
        "raw_data": RAW_DIR.exists(),
        "raw_path": str(RAW_DIR),
        "registered_datasets": len(registry.all()),
    }


@app.get("/api/datasets")
def datasets() -> dict[str, Any]:
    """Return both the physical raw tree and the project's dataset registry."""
    if not RAW_DIR.exists():
        return {"raw_exists": False, "datasets": [], "registry": []}

    result = []
    for category in sorted(RAW_DIR.iterdir(), key=lambda p: p.name.lower()):
        if category.is_dir():
            result.append({"name": category.name, **_scan_directory(category)})

    registry = create_default_registry()
    registry_data = []
    for item in registry.all():
        info = item.validate()
        info.update({
            "modality": item.modality,
            "description": item.description,
            "task": item.task,
            "tags": item.tags,
        })
        registry_data.append(info)

    return {"raw_exists": True, "datasets": result, "registry": registry_data}


@app.get("/api/pipeline")
def pipeline() -> dict[str, Any]:
    """Return a dry-run plan for all datasets currently available."""
    return build_pipeline()


@app.post("/api/pipeline/validate")
def validate_pipeline(request: PipelineRequest) -> dict[str, Any]:
    """Validate a user-selected set without modifying or processing raw data."""
    return build_pipeline(request.datasets or None)
