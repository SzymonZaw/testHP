from __future__ import annotations

from fastapi import APIRouter

from .database import status

router = APIRouter(tags=["database"])


@router.get("/api/system/database")
def database_status():
    return status()
