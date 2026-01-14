# app/api/routers/sensors_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database.database import Database
from app.services.runtime_state import RuntimeState
from app.services.sensor_registry_service import SensorRegistryService

router = APIRouter(prefix="/sensors", tags=["sensors"])


class SensorCreateIn(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(pattern="^(thermal_zone|hwmon)$")
    path: str = Field(min_length=1)
    enabled: bool = True


class SensorUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    path: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


def _db() -> Database:
    return RuntimeState.db()


@router.post("/auto-detect")
def auto_detect() -> dict:
    svc = SensorRegistryService(db=_db())
    return {"created": svc.auto_detect_default_sensors()}


@router.get("")
def list_sensors() -> list[dict]:
    return _db().sensors.list()


@router.post("")
def create_sensor(payload: SensorCreateIn) -> dict:
    try:
        return _db().sensors.create(
            name=payload.name,
            sensor_type=payload.type,
            path=payload.path,
            enabled=payload.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{sensor_id}")
def get_sensor(sensor_id: int) -> dict:
    try:
        return _db().sensors.get(sensor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{sensor_id}")
def update_sensor(sensor_id: int, payload: SensorUpdateIn) -> dict:
    try:
        return _db().sensors.update(sensor_id=sensor_id, name=payload.name, path=payload.path, enabled=payload.enabled)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{sensor_id}")
def delete_sensor(sensor_id: int) -> dict:
    try:
        return _db().sensors.delete(sensor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))