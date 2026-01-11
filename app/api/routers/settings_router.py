# app/api/routers/settings_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database.database import Database
from app.services.runtime_state import RuntimeState

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdateIn(BaseModel):
    unit_display: str | None = Field(default=None, pattern="^(C|F|K)$")

    loop_interval_s: float | None = Field(default=None, gt=0)
    smoothing_window_s: float | None = Field(default=None, ge=0)
    hysteresis_c: float | None = Field(default=None, ge=0)

    kickstart_enabled: bool | None = None
    kickstart_duty_percent: int | None = Field(default=None, ge=0, le=100)
    kickstart_ms: int | None = Field(default=None, ge=0, le=5000)

    hard_limit_c: float | None = Field(default=None, ge=0)
    hard_limit_margin_c: float | None = Field(default=None, ge=0, le=20)

    pwm_frequency_hz: int | None = Field(default=None, gt=0)


def _db() -> Database:
    return RuntimeState.db()


@router.get("")
def get_settings() -> dict:
    return _db().settings.get_all()


@router.patch("")
def update_settings(payload: SettingsUpdateIn) -> dict:
    try:
        return _db().settings.update_from_payload(payload.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))