# app/services/sensor_registry_service.py
import os
from typing import List, Dict, Any

from app.database.database import Database


class SensorRegistryService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def auto_detect_default_sensors(self) -> List[Dict[str, Any]]:
        created: List[Dict[str, Any]] = []

        # Default CPU thermal zone.
        cpu_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(cpu_path):
            try:
                created.append(self._db.sensors.create(name="cpu", sensor_type="thermal_zone", path=cpu_path, enabled=True))
            except ValueError:
                pass

        return created