# app/database/schemas/events.py
import sqlite3
from typing import Optional, Dict, Any, List
from app.core.time_utils import now_ts
from app.database.database_base import DatabaseBase


class Events(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                context TEXT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_events_created_at ON events(created_at);
            """
        )

    def create(self, level: str, message: str, context: Optional[str] = None,
               conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        level = (level or "").strip().upper() or "INFO"
        message = (message or "").strip()
        if not message:
            raise ValueError("message must not be empty")

        c, close = self._use_conn(conn)
        try:
            now = now_ts()
            c.execute(
                "INSERT INTO events(level, message, context, created_at) VALUES(?, ?, ?, ?)",
                (level, message, context, now),
            )
            c.commit()
            row = c.execute(
                "SELECT id, level, message, context, created_at FROM events WHERE id = last_insert_rowid()"
            ).fetchone()
            if not row:
                raise ValueError("Failed to create event")
            return dict(row)
        finally:
            if close:
                c.close()

    def list_recent(self, limit: int = 100, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        c, close = self._use_conn(conn)
        try:
            rows = c.execute(
                "SELECT id, level, message, context, created_at FROM events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            if close:
                c.close()