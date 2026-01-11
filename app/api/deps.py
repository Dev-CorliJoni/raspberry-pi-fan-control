# app/api/deps.py
from fastapi import Request

from app.database.database import Database
from app.services.runtime_state import RuntimeState


def get_db(request: Request) -> Database:
    # Prefer FastAPI app state. Fallback to RuntimeState for robustness.
    db = getattr(request.app.state, "db", None)
    if db is not None:
        return db

    return RuntimeState.db()