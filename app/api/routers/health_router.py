# app/api/routers/health_router.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict:
    # A stricter readiness is exposed via /setup/status.
    return {"status": "ok"}