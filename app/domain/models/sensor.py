# app/domain/models/sensor.py
from pydantic import BaseModel, ConfigDict, Field


class SensorModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(min_length=1)
    type: str = Field(pattern="^(thermal_zone|hwmon)$")
    path: str = Field(min_length=1)
    enabled: bool
    created_at: float
    updated_at: float