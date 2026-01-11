# app/domain/models/settings.py
from pydantic import BaseModel, Field


class SettingsModel(BaseModel):
    unit_display: str = Field(pattern="^(C|F|K)$")

    loop_interval_s: float = Field(gt=0)
    smoothing_window_s: float = Field(ge=0)
    hysteresis_c: float = Field(ge=0)

    kickstart_enabled: bool
    kickstart_duty_percent: int = Field(ge=0, le=100)
    kickstart_ms: int = Field(ge=0, le=5000)

    hard_limit_c: float = Field(ge=0)
    hard_limit_margin_c: float = Field(ge=0, le=20)

    pwm_frequency_hz: int = Field(gt=0)