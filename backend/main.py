from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks

from .app import PipelineRequest, app, run_pipeline

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _set_job(job_id: str, **values: Any) -> None:
    with _LOCK:
        _JOBS.setdefault(job_id, {}).update(values)


def _execute(job_id: str, selected: list[str]) -> None:
    try:
        # Status changes are tied to the real pipeline operation. We do not
        # create synthetic measurements or claim an intermediate result.
        _set_job(job_id, current_stage="input", progress=5)
        _set_job(job_id, current_stage="ingestion", progress=15)
        result = run_pipeline(selected)
        _set_job(job_id, current_stage="validation", progress=55)
        _set_job(job_id, current_stage="normalization", progress=70)
        _set_job(job_id, current_stage="fusion", progress=85)
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
