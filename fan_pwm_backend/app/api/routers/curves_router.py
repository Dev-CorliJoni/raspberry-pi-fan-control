# app/api/routers/curves_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database.database import Database
from app.services.runtime_state import RuntimeState
from app.core.units import display_to_c

router = APIRouter(tags=["curves"])


class CurveCreateIn(BaseModel):
    name: str = Field(min_length=1)


class CurveUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)


class PointCreateIn(BaseModel):
    temp: float
    duty_percent: int = Field(ge=0, le=100)


class PointBulkIn(BaseModel):
    points: list[PointCreateIn]


class PointUpdateIn(BaseModel):
    temp: float | None = None
    duty_percent: int | None = Field(default=None, ge=0, le=100)


def _db() -> Database:
    return RuntimeState.db()


@router.get("/sensors/{sensor_id}/curves")
def list_curves(sensor_id: int) -> list[dict]:
    return _db().curves.list(sensor_id=sensor_id)


@router.post("/sensors/{sensor_id}/curves")
def create_curve(sensor_id: int, payload: CurveCreateIn) -> dict:
    try:
        return _db().curves.create(sensor_id=sensor_id, name=payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/curves/{curve_id}")
def get_curve(curve_id: int) -> dict:
    try:
        return _db().curves.get(curve_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/curves/{curve_id}")
def update_curve(curve_id: int, payload: CurveUpdateIn) -> dict:
    try:
        return _db().curves.update(curve_id=curve_id, name=payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/curves/{curve_id}")
def delete_curve(curve_id: int) -> dict:
    try:
        return _db().curves.delete(curve_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/curves/{curve_id}/activate")
def activate_curve(curve_id: int) -> dict:
    try:
        return _db().curves.activate(curve_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/curves/{curve_id}/points")
def list_points(curve_id: int) -> list[dict]:
    return _db().curve_points.list(curve_id=curve_id)


@router.post("/curves/{curve_id}/points")
def create_point(curve_id: int, payload: PointCreateIn, unit: str = "C") -> dict:
    try:
        temp_c = round(display_to_c(payload.temp, unit), 1)
        return _db().curve_points.create(curve_id=curve_id, temp_c=temp_c, duty_percent=payload.duty_percent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/curves/{curve_id}/points")
def replace_points(curve_id: int, payload: PointBulkIn, unit: str = "C") -> dict:
    try:
        pts = [(round(display_to_c(p.temp, unit), 1), p.duty_percent) for p in payload.points]
        _db().curve_points.replace_all(curve_id=curve_id, points=pts)
        return {"points": _db().curve_points.list(curve_id=curve_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/points/{point_id}")
def update_point(point_id: int, payload: PointUpdateIn, unit: str = "C") -> dict:
    try:
        temp_c = None if payload.temp is None else round(display_to_c(payload.temp, unit), 1)
        return _db().curve_points.update(point_id=point_id, temp_c=temp_c, duty_percent=payload.duty_percent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/points/{point_id}")
def delete_point(point_id: int) -> dict:
    try:
        return _db().curve_points.delete(point_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))