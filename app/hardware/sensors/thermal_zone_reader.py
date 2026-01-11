# app/hardware/sensors/thermal_zone_reader.py
from app.hardware.sensors.sensor_reader_base import SensorReaderBase


class ThermalZoneReader(SensorReaderBase):
    def read_celsius(self, path: str) -> float:
        # thermal_zone temp is typically reported as millidegrees Celsius.
        raw = _read_text(path)
        v = int(raw)
        return float(v) / 1000.0


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return (f.read() or "").strip()