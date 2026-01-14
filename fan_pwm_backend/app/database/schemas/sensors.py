# app/database/schemas/sensors.py
import os
import sqlite3
from typing import Optional, Dict, Any, List
from app.core.time_utils import now_ts
from app.database.database_base import DatabaseBase


class Sensors(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                path TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )

    def create(self, name: str, sensor_type: str, path: str, enabled: bool = True,
               conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            raise ValueError("Sensor name must not be empty")

        sensor_type = (sensor_type or "").strip().lower()
        if sensor_type not in ("thermal_zone", "hwmon"):
            raise ValueError("type must be 'thermal_zone' or 'hwmon'")

        path = (path or "").strip()
        if not path or not path.startswith("/"):
            raise ValueError("path must be an absolute filesystem path")

        if not os.path.exists(path):
            raise ValueError("path does not exist on this system")

        c, close = self._use_conn(conn)
        try:
            now = now_ts()
            c.execute(
                "INSERT OR IGNORE INTO sensors(name, type, path, enabled, created_at, updated_at) VALUES(?, ?, ?, ?, ?, ?)",
                (name, sensor_type, path, 1 if enabled else 0, now, now),
            )
            c.commit()

            row = c.execute(
                "SELECT id, name, type, path, enabled, created_at, updated_at FROM sensors WHERE name = ?",
                (name,),
            ).fetchone()
            if not row:
                raise ValueError("Failed to create sensor")
            out = dict(row)
            out["enabled"] = bool(out["enabled"])
            return out
        finally:
            if close:
                c.close()

    def get(self, sensor_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute(
                "SELECT id, name, type, path, enabled, created_at, updated_at FROM sensors WHERE id = ?",
                (sensor_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown sensor_id")
            out = dict(row)
            out["enabled"] = bool(out["enabled"])
            return out
        finally:
            if close:
                c.close()

    def list(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        c, close = self._use_conn(conn)
        try:
            rows = c.execute(
                "SELECT id, name, type, path, enabled, created_at, updated_at FROM sensors ORDER BY name"
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["enabled"] = bool(d["enabled"])
                out.append(d)
            return out
        finally:
            if close:
                c.close()

    def update(self, sensor_id: int, name: Optional[str] = None, path: Optional[str] = None,
               enabled: Optional[bool] = None, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            current = c.execute("SELECT id, name, type, path, enabled FROM sensors WHERE id = ?", (sensor_id,)).fetchone()
            if not current:
                raise ValueError("Unknown sensor_id")

            new_name = (name.strip() if name is not None else str(current["name"])).strip()
            if not new_name:
                raise ValueError("Sensor name must not be empty")

            new_path = (path.strip() if path is not None else str(current["path"])).strip()
            if not new_path.startswith("/"):
                raise ValueError("path must be an absolute filesystem path")
            if not os.path.exists(new_path):
                raise ValueError("path does not exist on this system")

            new_enabled = int(bool(enabled)) if enabled is not None else int(current["enabled"])
            now = now_ts()

            c.execute(
                "UPDATE sensors SET name = ?, path = ?, enabled = ?, updated_at = ? WHERE id = ?",
                (new_name, new_path, new_enabled, now, sensor_id),
            )
            c.commit()
            return self.get(sensor_id, conn=c)
        finally:
            if close:
                c.close()

    def delete(self, sensor_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute(
                "SELECT id, name, type, path, enabled, created_at, updated_at FROM sensors WHERE id = ?",
                (sensor_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown sensor_id")

            c.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
            c.commit()

            out = dict(row)
            out["enabled"] = bool(out["enabled"])
            return out
        finally:
            if close:
                c.close()