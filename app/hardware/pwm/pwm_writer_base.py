# app/hardware/pwm/pwm_writer_base.py
from abc import ABC, abstractmethod


class PwmWriterBase(ABC):
    @abstractmethod
    def ensure_exported(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_frequency_hz(self, hz: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_duty_percent(self, duty_percent: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def enable(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def disable(self) -> None:
        raise NotImplementedError