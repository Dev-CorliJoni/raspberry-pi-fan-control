# app/domain/models/curve.py
from pydantic import BaseModel, ConfigDict, Field


class CurveModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    name: str = Field(min_length=1)
    is_active: bool
    created_at: float
    updated_at: float