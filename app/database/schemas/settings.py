# app/database/schemas/settings.py
import sqlite3
from typing import Optional, Dict, Any
from app.core.time_utils import now_ts
from app.database.database_base import DatabaseBase


DEFAULTS: Dict[str, str] = {
    # Units
    "unit_display": "C",

    # Control loop behavior
    "loop_interval_s": "1.0",
    "smoothing_window_s": "15.0",
    "hysteresis_c": "1.0",

    # Kickstart
    "kickstart_enabled": "1",
    "kickstart_duty_percent": "100",
    "kickstart_ms": "300",

    # Safety
    "hard_limit_c": "80.0",
    "hard_limit_margin_c": "5.0",

    # PWM
    "pwm_frequency_hz": "25000",
}


class Settings(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )
        # Seed defaults without overwriting existing values.
        now = now_ts()
        for k, v in DEFAULTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings(key, value, updated_at) VALUES(?, ?, ?)",
                (k, v, now),
            )

    def get(self, key: str, default: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> Optional[str]:
        key = (key or "").strip()
        if not key:
            return default
        c, close = self._use_conn(conn)
        try:
            row = c.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
            if not row:
                return default
            return str(row["value"])
        finally:
            if close:
                c.close()

    def set(self, key: str, value: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        key = (key or "").strip()
        if not key:
            raise ValueError("key must not be empty")

        c, close = self._use_conn(conn)
        try:
            now = now_ts()
            c.execute(
                "INSERT OR REPLACE INTO app_settings(key, value, updated_at) VALUES(?, ?, ?)",
                (key, str(value), now),
            )
            c.commit()
            row = c.execute("SELECT key, value, updated_at FROM app_settings WHERE key = ?", (key,)).fetchone()
            if not row:
                raise ValueError("Failed to set setting")
            return dict(row)
        finally:
            if close:
                c.close()

    def get_all(self, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            rows = c.execute("SELECT key, value, updated_at FROM app_settings ORDER BY key").fetchall()
            out = {}
            for r in rows:
                out[str(r["key"])] = str(r["value"])
            return out
        finally:
            if close:
                c.close()

    def update_from_payload(self, payload: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        c, close = self._use_conn(conn)
        try:
            for k, v in payload.items():
                self.set(str(k), str(v), conn=c)
            return self.get_all(conn=c)
        finally:
            if close:
                c.close()