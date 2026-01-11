# app/services/runtime_state.py
import threading
import time
from typing import Optional, Dict, Any

from app.database.database import Database


class RuntimeState:
    _lock = threading.Lock()

    _db: Optional[Database] = None

    _current_duty_percent: int = 0
    _target_duty_percent: int = 0
    _mode: str = "auto"  # "auto" | "override"
    _override_duty_percent: Optional[int] = None
    _override_until_ts: Optional[float] = None

    _last_temps_c: Dict[str, float] = {}
    _last_errors: list[dict] = []

    @classmethod
    def bind_db(cls, db: Database) -> None:
        with cls._lock:
            cls._db = db

    @classmethod
    def db(cls) -> Database:
        with cls._lock:
            if cls._db is None:
                raise RuntimeError("Database not bound")
            return cls._db

    @classmethod
    def set_current_duty(cls, duty: int) -> None:
        with cls._lock:
            cls._current_duty_percent = int(duty)

    @classmethod
    def set_target_duty(cls, duty: int) -> None:
        with cls._lock:
            cls._target_duty_percent = int(duty)

    @classmethod
    def set_temps(cls, temps_c: Dict[str, float]) -> None:
        with cls._lock:
            cls._last_temps_c = dict(temps_c)

    @classmethod
    def add_error(cls, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        with cls._lock:
            cls._last_errors.insert(0, {"ts": time.time(), "message": message, "context": context or {}})
            cls._last_errors = cls._last_errors[:50]

    @classmethod
    def set_override(cls, duty_percent: int, timeout_s: Optional[int]) -> None:
        duty_percent = int(duty_percent)
        if duty_percent < 0 or duty_percent > 100:
            raise ValueError("duty_percent must be 0..100")

        with cls._lock:
            cls._mode = "override"
            cls._override_duty_percent = duty_percent
            if timeout_s is None:
                cls._override_until_ts = None
            else:
                cls._override_until_ts = time.time() + float(timeout_s)

    @classmethod
    def clear_override(cls) -> None:
        with cls._lock:
            cls._mode = "auto"
            cls._override_duty_percent = None
            cls._override_until_ts = None

    @classmethod
    def get_effective_override(cls) -> Optional[int]:
        with cls._lock:
            if cls._mode != "override":
                return None
            if cls._override_until_ts is not None and time.time() >= cls._override_until_ts:
                cls._mode = "auto"
                cls._override_duty_percent = None
                cls._override_until_ts = None
                return None
            return cls._override_duty_percent

    @classmethod
    def override_snapshot(cls) -> dict:
        with cls._lock:
            return {
                "mode": cls._mode,
                "override_duty_percent": cls._override_duty_percent,
                "override_until_ts": cls._override_until_ts,
            }

    @classmethod
    def snapshot(cls) -> dict:
        with cls._lock:
            return {
                "mode": cls._mode,
                "current_duty_percent": cls._current_duty_percent,
                "target_duty_percent": cls._target_duty_percent,
                "override": {
                    "duty_percent": cls._override_duty_percent,
                    "until_ts": cls._override_until_ts,
                },
                "temps_c": dict(cls._last_temps_c),
                "last_errors": list(cls._last_errors),
            }