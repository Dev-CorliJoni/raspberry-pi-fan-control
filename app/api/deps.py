# app/api/deps.py
from app.database.database import Database


def get_db() -> Database:
    # Kept for future dependency injection expansion.
    raise RuntimeError("Dependency injection not wired in this minimal version")