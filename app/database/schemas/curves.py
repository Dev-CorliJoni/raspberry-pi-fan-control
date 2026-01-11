# app/database/schemas/curves.py
import sqlite3
from typing import Optional, Dict, Any, List
from app.core.time_utils import now_ts
from app.database.database_base import DatabaseBase


class Curves(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS curves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY(sensor_id) REFERENCES sensors(id) ON DELETE CASCADE,
                UNIQUE(sensor_id, name)
            );
            CREATE INDEX IF NOT EXISTS ix_curves_sensor_id ON curves(sensor_id);
            """
        )

    def create(self, sensor_id: int, name: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        name = (name or "").strip()
        if not name:
            raise ValueError("Curve name must not be empty")

        c, close = self._use_conn(conn)
        try:
            sensor_row = c.execute("SELECT id FROM sensors WHERE id = ?", (sensor_id,)).fetchone()
            if not sensor_row:
                raise ValueError("Unknown sensor_id")

            now = now_ts()
            c.execute(
                "INSERT OR IGNORE INTO curves(sensor_id, name, is_active, created_at, updated_at) VALUES(?, ?, 0, ?, ?)",
                (sensor_id, name, now, now),
            )
            c.commit()

            row = c.execute(
                "SELECT id, sensor_id, name, is_active, created_at, updated_at FROM curves WHERE sensor_id = ? AND name = ?",
                (sensor_id, name),
            ).fetchone()
            if not row:
                raise ValueError("Failed to create curve")
            out = dict(row)
            out["is_active"] = bool(out["is_active"])
            return out
        finally:
            if close:
                c.close()

    def get(self, curve_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute(
                "SELECT id, sensor_id, name, is_active, created_at, updated_at FROM curves WHERE id = ?",
                (curve_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown curve_id")
            out = dict(row)
            out["is_active"] = bool(out["is_active"])
            return out
        finally:
            if close:
                c.close()

    def list(self, sensor_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        c, close = self._use_conn(conn)
        try:
            rows = c.execute(
                "SELECT id, sensor_id, name, is_active, created_at, updated_at FROM curves WHERE sensor_id = ? ORDER BY name",
                (sensor_id,),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["is_active"] = bool(d["is_active"])
                out.append(d)
            return out
        finally:
            if close:
                c.close()

    def update(self, curve_id: int, name: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            current = c.execute("SELECT id, sensor_id, name FROM curves WHERE id = ?", (curve_id,)).fetchone()
            if not current:
                raise ValueError("Unknown curve_id")

            new_name = (name.strip() if name is not None else str(current["name"])).strip()
            if not new_name:
                raise ValueError("Curve name must not be empty")

            now = now_ts()
            c.execute("UPDATE curves SET name = ?, updated_at = ? WHERE id = ?", (new_name, now, curve_id))
            c.commit()
            return self.get(curve_id, conn=c)
        finally:
            if close:
                c.close()

    def activate(self, curve_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute("SELECT id, sensor_id FROM curves WHERE id = ?", (curve_id,)).fetchone()
            if not row:
                raise ValueError("Unknown curve_id")
            sensor_id = int(row["sensor_id"])

            now = now_ts()
            c.execute("UPDATE curves SET is_active = 0, updated_at = ? WHERE sensor_id = ?", (now, sensor_id))
            c.execute("UPDATE curves SET is_active = 1, updated_at = ? WHERE id = ?", (now, curve_id))
            c.commit()
            return self.get(curve_id, conn=c)
        finally:
            if close:
                c.close()

    def delete(self, curve_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute(
                "SELECT id, sensor_id, name, is_active, created_at, updated_at FROM curves WHERE id = ?",
                (curve_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown curve_id")

            c.execute("DELETE FROM curves WHERE id = ?", (curve_id,))
            c.commit()

            out = dict(row)
            out["is_active"] = bool(out["is_active"])
            return out
        finally:
            if close:
                c.close()