# app/domain/models/setup_status.py
from pydantic import BaseModel


class SetupStatusModel(BaseModel):
    os: dict[str, str]
    running_in_home_assistant_addon: bool

    thermal_ok: bool
    pwm_sysfs_present: bool
    pwm_write_access: bool
    pwmchips: list[str]