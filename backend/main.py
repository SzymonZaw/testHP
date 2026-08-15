from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks

from .app import PipelineRequest, app, build_findings, dataset_registry, validate_dataset

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _set_job(job_id: str, **values: Any) -> None:
    with _LOCK:
        _JOBS.setdefault(job_id, {}).update(values)


def _execute(job_id: str, selected: list[str]) -> None:
    try:
        _set_job(job_id, current_stage="input", progress=5)
        registry = dataset_registry()
        by_name = {x["name"]: x for x in registry}
        chosen = selected or list(by_name)
        missing = [name for name in chosen if name not in by_name]

        _set_job(job_id, current_stage="ingestion", progress=25)
        validations = {name: validate_dataset(by_name[name]) for name in chosen if name in by_name}
        usable_items = [x for x in validations.values() if x["available"] and x["supported_files"] > 0]

        _set_job(job_id, current_stage="validation", progress=45)
        modalities = sorted({x["modality"] for x in usable_items})
        total_files = sum(x["supported_files"] for x in usable_items)
        total_bytes = sum(x["bytes"] for x in usable_items)
        warnings = [w for item in validations.values() for w in item["warnings"]]

        _set_job(job_id, current_stage="normalization", progress=65)
        findings = build_findings(usable_items)

        _set_job(job_id, current_stage="fusion", progress=80)
        steps = [
            {"id": "input", "name": "Input", "purpose": "Identify selected research datasets", "status": "ok" if not missing else "warning"},
            {"id": "ingestion", "name": "Ingestion", "purpose": "Read available files from data/raw", "status": "ok" if usable_items else "warning"},
            {"id": "validation", "name": "Validation", "purpose": "Check files, formats and empty inputs", "status": "ok" if not warnings and not missing else "warning"},
            {"id": "normalization", "name": "Normalization", "purpose": "Convert sources into common observations", "status": "ok" if usable_items else "warning"},
            {"id": "fusion", "name": "Multimodal fusion", "purpose": "Aggregate dataset-level evidence without inventing subject links", "status": "ok" if usable_items else "warning"},
            {"id": "results", "name": "Research view", "purpose": "Present measured evidence, coverage and limitations", "status": "ok" if usable_items else "warning"},
        ]
        result = {
            "status": "ready" if usable_items and not missing else "warning",
            "selected": chosen,
            "missing": missing,
            "datasets": list(validations.values()),
            "steps": steps,
            "summary": {"datasets": len(usable_items), "files": total_files, "bytes": total_bytes, "modalities": modalities, "linked_subjects": 0},
            "warnings": warnings + (["Subject-level links are not inferred without a shared identifier."] if usable_items else []),
            "results": {
                "evidence_level": "dataset-level measured evidence",
                "biological_inference": "Measured input characteristics are available; biological conclusions are not inferred.",
                "next_action": "Review the measured observations below. A biological result is shown only after a validated modality-specific analysis is implemented and executed.",
                "findings": findings,
                "biological_results": [],
            },
        }
        _set_job(job_id, current_stage="results", progress=100, status="completed", result=result)
    except Exception as exc:
        _set_job(job_id, status="failed", current_stage="error", progress=100, error=f"{type(exc).__name__}: {exc}")


@app.post("/api/run/background")
def run_background(request: PipelineRequest, background_tasks: BackgroundTasks):
    selected = list(request.datasets or [])
    job_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    _set_job(job_id, status="running", current_stage="input", progress=0, result=None, error=None)
    background_tasks.add_task(_execute, job_id, selected)
    return {"job_id": job_id, "status": "running", "current_stage": "input", "progress": 0}


@app.get("/api/run/background/{job_id}")
def run_background_status(job_id: str):
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return {"job_id": job_id, "status": "not_found"}
        return {"job_id": job_id, **job}
