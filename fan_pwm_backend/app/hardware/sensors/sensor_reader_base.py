# app/hardware/sensors/sensor_reader_base.py
from abc import ABC, abstractmethod


class SensorReaderBase(ABC):
    @abstractmethod
    def read_celsius(self, path: str) -> float:
        raise NotImplementedError