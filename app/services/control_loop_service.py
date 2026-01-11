# app/services/control_loop_service.py
import asyncio
import logging
import os
import time
from collections import deque
from typing import Dict, Tuple, Optional

from app.core.config import AppConfig
from app.database.database import Database
from app.hardware.sensors.thermal_zone_reader import ThermalZoneReader
from app.hardware.sensors.hwmon_reader import HwmonReader
from app.services.curve_engine import CurveEngine
from app.services.pwm_service import PwmService
from app.services.safety_service import SafetyService
from app.services.runtime_state import RuntimeState

logger = logging.getLogger(__name__)


class ControlLoopService:
    def __init__(self, db: Database, config: AppConfig) -> None:
        self._db = db
        self._config = config
        RuntimeState.bind_db(db)

        self._stop = False

        self._thermal_reader = ThermalZoneReader()
        self._hwmon_reader = HwmonReader()
        self._curve_engine = CurveEngine()
        self._safety = SafetyService()

        self._pwm = PwmService(pwm_chip=config.pwm_chip, pwm_channel=config.pwm_channel)
        self._pwm_initialized = False

        self._temp_history: Dict[int, deque[Tuple[float, float]]] = {}
        self._last_temp_used: Dict[int, float] = {}

    def stop(self) -> None:
        self._stop = True

    async def run(self) -> None:
        self._ensure_seeded()

        while not self._stop:
            started = time.time()
            try:
                await self._tick()
            except Exception:
                logger.exception("Control loop tick failed")
                self._db.events.create(level="ERROR", message="control_loop_tick_failed", context=None)
                RuntimeState.add_error("control_loop_tick_failed")

            interval_s = _read_float(self._db.settings.get("loop_interval_s", "1.0"), 1.0)
            elapsed = time.time() - started
            sleep_s = max(0.05, interval_s - elapsed)
            await asyncio.sleep(sleep_s)

        try:
            self._pwm.disable()
        except Exception:
            pass

    async def _tick(self) -> None:
        settings = self._db.settings.get_all()

        unit_display = (settings.get("unit_display", "C") or "C").upper()
        loop_interval_s = _read_float(settings.get("loop_interval_s", "1.0"), 1.0)
        smoothing_window_s = _read_float(settings.get("smoothing_window_s", "15.0"), 15.0)
        hysteresis_c = _read_float(settings.get("hysteresis_c", "1.0"), 1.0)

        kickstart_enabled = _read_bool(settings.get("kickstart_enabled", "1"), True)
        kickstart_duty = _read_int(settings.get("kickstart_duty_percent", "100"), 100)
        kickstart_ms = _read_int(settings.get("kickstart_ms", "300"), 300)

        hard_limit_c = _read_float(settings.get("hard_limit_c", "80.0"), 80.0)
        hard_limit_margin_c = _read_float(settings.get("hard_limit_margin_c", "5.0"), 5.0)

        pwm_frequency_hz = _read_int(settings.get("pwm_frequency_hz", str(self._config.pwm_frequency_hz)), self._config.pwm_frequency_hz)

        # Override mode
        override = RuntimeState.get_effective_override()
        if override is not None:
            target = int(override)
            safety_decision = self._safety.apply(target, max_temp_c=None, hard_limit_c=hard_limit_c, margin_c=0.0)
            await self._apply_pwm(safety_decision.duty_percent, pwm_frequency_hz, kickstart_enabled, kickstart_duty, kickstart_ms)
            RuntimeState.set_target_duty(target)
            return

        # Auto mode: read enabled sensors
        sensors = [s for s in self._db.sensors.list() if s.get("enabled")]
        temps_c: Dict[str, float] = {}
        max_temp: Optional[float] = None

        # Compute per-sensor duty (only if sensor has an active curve)
        duties: list[int] = []
        for s in sensors:
            sensor_id = int(s["id"])
            sensor_name = str(s["name"])
            sensor_type = str(s["type"])
            sensor_path = str(s["path"])

            temp_c = self._read_sensor_temp(sensor_id, sensor_type, sensor_path, smoothing_window_s, loop_interval_s, hysteresis_c)
            if temp_c is not None:
                temps_c[sensor_name] = temp_c
                max_temp = temp_c if max_temp is None else max(max_temp, temp_c)

            active_curve = self._get_active_curve(sensor_id)
            if active_curve is None:
                continue

            points = self._db.curve_points.list(curve_id=int(active_curve["id"]))
            point_pairs = [(float(p["temp_c"]), int(p["duty_percent"])) for p in points]

            if temp_c is None:
                continue

            res = self._curve_engine.evaluate(point_pairs, temp_c)
            duties.append(res.duty_percent)

        RuntimeState.set_temps(temps_c)

        target = max(duties) if duties else 0
        RuntimeState.set_target_duty(target)

        safety_decision = self._safety.apply(target, max_temp_c=max_temp, hard_limit_c=hard_limit_c, margin_c=hard_limit_margin_c)
        await self._apply_pwm(safety_decision.duty_percent, pwm_frequency_hz, kickstart_enabled, kickstart_duty, kickstart_ms)

    async def _apply_pwm(self, duty_percent: int, pwm_frequency_hz: int,
                        kickstart_enabled: bool, kickstart_duty: int, kickstart_ms: int) -> None:
        try:
            if not self._pwm_initialized:
                self._pwm.try_init(frequency_hz=pwm_frequency_hz)
                self._pwm_initialized = True

            self._pwm.set_duty(
                duty_percent=duty_percent,
                kickstart_enabled=kickstart_enabled,
                kickstart_duty=kickstart_duty,
                kickstart_ms=kickstart_ms,
            )
            RuntimeState.set_current_duty(duty_percent)
        except Exception as e:
            # Fail-safe: attempt 100% if possible; otherwise keep running and report.
            logger.exception("PWM write failed")
            self._db.events.create(level="ERROR", message="pwm_write_failed", context=str(e))
            RuntimeState.add_error("pwm_write_failed", {"error": str(e)})

            try:
                if self._pwm_initialized:
                    self._pwm.set_duty(
                        duty_percent=100,
                        kickstart_enabled=False,
                        kickstart_duty=100,
                        kickstart_ms=0,
                    )
                    RuntimeState.set_current_duty(100)
            except Exception:
                pass

            self._pwm_initialized = False

    def _read_sensor_temp(self, sensor_id: int, sensor_type: str, sensor_path: str,
                         smoothing_window_s: float, loop_interval_s: float, hysteresis_c: float) -> Optional[float]:
        try:
            if not os.path.exists(sensor_path):
                raise ValueError("sensor_path_missing")

            if sensor_type == "thermal_zone":
                raw = self._thermal_reader.read_celsius(sensor_path)
            elif sensor_type == "hwmon":
                raw = self._hwmon_reader.read_celsius(sensor_path)
            else:
                raise ValueError("unknown_sensor_type")

            raw = round(float(raw), 1)

            # History (moving average)
            if smoothing_window_s > 0:
                dq = self._temp_history.get(sensor_id)
                if dq is None:
                    dq = deque()
                    self._temp_history[sensor_id] = dq

                now = time.time()
                dq.append((now, raw))

                cutoff = now - float(smoothing_window_s)
                while dq and dq[0][0] < cutoff:
                    dq.popleft()

                avg = sum(v for _, v in dq) / max(1, len(dq))
                temp_c = round(float(avg), 1)
            else:
                temp_c = raw

            # Hysteresis (freeze temp within hysteresis band)
            if hysteresis_c > 0:
                last = self._last_temp_used.get(sensor_id)
                if last is None:
                    self._last_temp_used[sensor_id] = temp_c
                else:
                    if abs(temp_c - last) < float(hysteresis_c):
                        temp_c = last
                    else:
                        self._last_temp_used[sensor_id] = temp_c

            return temp_c
        except Exception as e:
            self._db.events.create(level="ERROR", message="sensor_read_failed", context=f"{sensor_id}:{sensor_path}:{e}")
            RuntimeState.add_error("sensor_read_failed", {"sensor_id": sensor_id, "path": sensor_path, "error": str(e)})
            return None

    def _get_active_curve(self, sensor_id: int) -> Optional[dict]:
        curves = self._db.curves.list(sensor_id=sensor_id)
        for c in curves:
            if c.get("is_active"):
                return c
        return None

    def _ensure_seeded(self) -> None:
        # Ensure we have at least one default sensor and a default curve if none exist.
        try:
            if not self._db.sensors.list():
                cpu_path = "/sys/class/thermal/thermal_zone0/temp"
                if os.path.exists(cpu_path):
                    self._db.sensors.create(name="cpu", sensor_type="thermal_zone", path=cpu_path, enabled=True)

            sensors = self._db.sensors.list()
            for s in sensors:
                sensor_id = int(s["id"])
                curves = self._db.curves.list(sensor_id=sensor_id)
                if curves:
                    continue

                curve = self._db.curves.create(sensor_id=sensor_id, name="default")
                self._db.curves.activate(int(curve["id"]))

                # Default points: 20C->0%, 50C->50%, 80C->100%
                self._db.curve_points.replace_all(
                    curve_id=int(curve["id"]),
                    points=[(20.0, 0), (50.0, 50), (80.0, 100)],
                )
        except Exception:
            logger.exception("Failed to seed defaults")


def _read_int(raw: Optional[str], default: int) -> int:
    try:
        return int(str(raw).strip())
    except Exception:
        return int(default)


def _read_float(raw: Optional[str], default: float) -> float:
    try:
        return float(str(raw).strip())
    except Exception:
        return float(default)


def _read_bool(raw: Optional[str], default: bool) -> bool:
    if raw is None:
        return bool(default)
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return bool(default)