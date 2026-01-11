# app/api/routers/setup_router.py
from fastapi import APIRouter

from app.services.setup_service import SetupService
from app.services.runtime_state import RuntimeState

router = APIRouter(tags=["setup"])


@router.get("/setup/status")
def setup_status() -> dict:
    svc = SetupService()
    return svc.get_setup_status()


@router.get("/setup/next-step")
def setup_next_step() -> dict:
    svc = SetupService()
    st = svc.get_setup_status()
    return {"next_step": svc.get_next_step(st), "setup_status": st, "runtime": RuntimeState.snapshot()}