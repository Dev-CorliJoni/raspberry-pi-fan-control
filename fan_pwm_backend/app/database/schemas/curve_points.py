# app/database/schemas/curve_points.py
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from app.core.time_utils import now_ts
from app.database.database_base import DatabaseBase


class CurvePoints(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS curve_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curve_id INTEGER NOT NULL,
                temp_c REAL NOT NULL,
                duty_percent INTEGER NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY(curve_id) REFERENCES curves(id) ON DELETE CASCADE,
                UNIQUE(curve_id, temp_c)
            );
            CREATE INDEX IF NOT EXISTS ix_curve_points_curve_id ON curve_points(curve_id);
            """
        )

    def list(self, curve_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        c, close = self._use_conn(conn)
        try:
            rows = c.execute(
                "SELECT id, curve_id, temp_c, duty_percent, created_at, updated_at FROM curve_points WHERE curve_id = ? ORDER BY temp_c",
                (curve_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            if close:
                c.close()

    def create(self, curve_id: int, temp_c: float, duty_percent: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        if duty_percent < 0 or duty_percent > 100:
            raise ValueError("duty_percent must be 0..100")

        temp_c = float(temp_c)
        temp_c = round(temp_c, 1)

        c, close = self._use_conn(conn)
        try:
            curve_row = c.execute("SELECT id FROM curves WHERE id = ?", (curve_id,)).fetchone()
            if not curve_row:
                raise ValueError("Unknown curve_id")

            now = now_ts()
            c.execute(
                "INSERT OR REPLACE INTO curve_points(curve_id, temp_c, duty_percent, created_at, updated_at) VALUES(?, ?, ?, ?, ?)",
                (curve_id, temp_c, duty_percent, now, now),
            )
            c.commit()
            row = c.execute(
                "SELECT id, curve_id, temp_c, duty_percent, created_at, updated_at FROM curve_points WHERE curve_id = ? AND temp_c = ?",
                (curve_id, temp_c),
            ).fetchone()
            if not row:
                raise ValueError("Failed to create curve point")
            return dict(row)
        finally:
            if close:
                c.close()

    def replace_all(self, curve_id: int, points: List[Tuple[float, int]], conn: Optional[sqlite3.Connection] = None) -> None:
        c, close = self._use_conn(conn)
        try:
            curve_row = c.execute("SELECT id FROM curves WHERE id = ?", (curve_id,)).fetchone()
            if not curve_row:
                raise ValueError("Unknown curve_id")

            c.execute("DELETE FROM curve_points WHERE curve_id = ?", (curve_id,))
            now = now_ts()
            for temp_c, duty in points:
                if duty < 0 or duty > 100:
                    raise ValueError("duty_percent must be 0..100")
                c.execute(
                    "INSERT INTO curve_points(curve_id, temp_c, duty_percent, created_at, updated_at) VALUES(?, ?, ?, ?, ?)",
                    (curve_id, round(float(temp_c), 1), int(duty), now, now),
                )
            c.commit()
        finally:
            if close:
                c.close()

    def update(self, point_id: int, temp_c: Optional[float] = None, duty_percent: Optional[int] = None,
               conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            current = c.execute("SELECT id, curve_id, temp_c, duty_percent FROM curve_points WHERE id = ?", (point_id,)).fetchone()
            if not current:
                raise ValueError("Unknown point_id")

            new_temp = float(temp_c) if temp_c is not None else float(current["temp_c"])
            new_temp = round(new_temp, 1)

            new_duty = int(duty_percent) if duty_percent is not None else int(current["duty_percent"])
            if new_duty < 0 or new_duty > 100:
                raise ValueError("duty_percent must be 0..100")

            now = now_ts()
            c.execute(
                "UPDATE curve_points SET temp_c = ?, duty_percent = ?, updated_at = ? WHERE id = ?",
                (new_temp, new_duty, now, point_id),
            )
            c.commit()

            row = c.execute(
                "SELECT id, curve_id, temp_c, duty_percent, created_at, updated_at FROM curve_points WHERE id = ?",
                (point_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown point_id")
            return dict(row)
        finally:
            if close:
                c.close()

    def delete(self, point_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            row = c.execute(
                "SELECT id, curve_id, temp_c, duty_percent, created_at, updated_at FROM curve_points WHERE id = ?",
                (point_id,),
            ).fetchone()
            if not row:
                raise ValueError("Unknown point_id")

            c.execute("DELETE FROM curve_points WHERE id = ?", (point_id,))
            c.commit()
            return dict(row)
        finally:
            if close:
                c.close()