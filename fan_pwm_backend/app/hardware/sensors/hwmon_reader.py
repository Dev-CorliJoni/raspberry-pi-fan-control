# app/hardware/sensors/hwmon_reader.py
from app.hardware.sensors.sensor_reader_base import SensorReaderBase


class HwmonReader(SensorReaderBase):
    def read_celsius(self, path: str) -> float:
        # hwmon temp*_input is typically reported as millidegrees Celsius.
        raw = _read_text(path)
        v = int(raw)
        return float(v) / 1000.0


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return (f.read() or "").strip()