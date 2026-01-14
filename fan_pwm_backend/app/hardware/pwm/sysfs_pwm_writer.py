# app/hardware/pwm/sysfs_pwm_writer.py
import os
from app.hardware.pwm.pwm_writer_base import PwmWriterBase


class SysfsPwmWriter(PwmWriterBase):
    def __init__(self, pwm_chip: str, pwm_channel: int) -> None:
        self._chip = pwm_chip
        self._channel = int(pwm_channel)
        self._chip_path = os.path.join("/sys/class/pwm", self._chip)
        self._pwm_path = os.path.join(self._chip_path, f"pwm{self._channel}")

    def ensure_exported(self) -> None:
        if os.path.isdir(self._pwm_path):
            return
        export_path = os.path.join(self._chip_path, "export")
        _write_text(export_path, str(self._channel))

    def set_frequency_hz(self, hz: int) -> None:
        if hz <= 0:
            raise ValueError("hz must be > 0")
        self.ensure_exported()
        period_ns = int(1_000_000_000 // int(hz))
        period_path = os.path.join(self._pwm_path, "period")
        _write_text(period_path, str(period_ns))

    def set_duty_percent(self, duty_percent: int) -> None:
        duty_percent = int(duty_percent)
        if duty_percent < 0 or duty_percent > 100:
            raise ValueError("duty_percent must be 0..100")

        self.ensure_exported()
        period_ns = int(_read_text(os.path.join(self._pwm_path, "period")))
        duty_ns = int(period_ns * duty_percent / 100.0)
        duty_path = os.path.join(self._pwm_path, "duty_cycle")
        _write_text(duty_path, str(duty_ns))

    def enable(self) -> None:
        self.ensure_exported()
        _write_text(os.path.join(self._pwm_path, "enable"), "1")

    def disable(self) -> None:
        if not os.path.isdir(self._pwm_path):
            return
        _write_text(os.path.join(self._pwm_path, "enable"), "0")


def _write_text(path: str, value: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(value))


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return (f.read() or "").strip()