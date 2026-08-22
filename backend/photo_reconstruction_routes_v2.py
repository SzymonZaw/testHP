"""Stage 6-10 HTTP handlers kept separate so the existing stage-1-5 API remains stable."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .reconstruction_orchestrator import run, get_result, clear

router = APIRouter(prefix='/api/hand/photo-reconstruction/v2', tags=['photo-reconstruction-v2'])

class BuildRequest(BaseModel):
    subject_id: str
    timepoint: str = 'default'
    resolution: int = 24

class ClearRequest(BaseModel):
    subject_id: str
    timepoint: str = 'default'

@router.post('/build')
def build(req: BuildRequest):
    result = run(req.subject_id, req.timepoint, max(12, min(64, req.resolution)))
    if result.get('status') == 'blocked':
        raise HTTPException(status_code=400, detail=result['reason'])
    return result

@router.get('/result')
def result(subject_id: str = 'default', timepoint: str = 'default'):
    return {'reconstruction': get_result(subject_id, timepoint)}

@router.post('/clear')
def clear_result(req: ClearRequest):
    return {'cleared': clear(req.subject_id, req.timepoint)}
