# app/domain/models/curve_point.py
from pydantic import BaseModel, ConfigDict, Field


class CurvePointModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curve_id: int
    temp_c: float
    duty_percent: int = Field(ge=0, le=100)
    created_at: float
    updated_at: float