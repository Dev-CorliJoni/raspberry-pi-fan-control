# app/api/routers/control_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/control", tags=["control"])


class OverrideIn(BaseModel):
    duty_percent: int = Field(ge=0, le=100)
    timeout_s: int | None = Field(default=None, ge=1, le=24 * 3600)


@router.post("/override")
def set_override(payload: OverrideIn) -> dict:
    try:
        RuntimeState.set_override(duty_percent=payload.duty_percent, timeout_s=payload.timeout_s)
        return {"ok": True, "override": RuntimeState.override_snapshot()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auto")
def set_auto() -> dict:
    RuntimeState.clear_override()
    return {"ok": True, "override": RuntimeState.override_snapshot()}