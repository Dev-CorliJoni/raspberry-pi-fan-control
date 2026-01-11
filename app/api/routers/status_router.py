# app/api/routers/status_router.py
from fastapi import APIRouter

from app.services.runtime_state import RuntimeState

router = APIRouter(tags=["status"])


@router.get("/status")
def status() -> dict:
    return RuntimeState.snapshot()