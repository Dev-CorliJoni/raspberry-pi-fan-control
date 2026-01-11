# app/domain/models/status.py
from pydantic import BaseModel, Field


class StatusModel(BaseModel):
    mode: str = Field(pattern="^(auto|override)$")

    current_duty_percent: int = Field(ge=0, le=100)
    target_duty_percent: int = Field(ge=0, le=100)

    override_duty_percent: int | None = Field(default=None, ge=0, le=100)
    override_until_ts: float | None = None

    temps_c: dict[str, float]
    last_errors: list[dict]