# app/core/config.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    data_dir: str
    log_level: str

    pwm_pin_physical: int
    pwm_chip: str
    pwm_channel: int
    pwm_frequency_hz: int

    @staticmethod
    def from_env() -> "AppConfig":
        data_dir = os.getenv("DATA_DIR", "/data").strip() or "/data"
        log_level = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"

        pwm_pin_physical = int(os.getenv("PWM_PIN", "33"))
        pwm_chip = os.getenv("PWM_CHIP", "pwmchip0").strip() or "pwmchip0"
        pwm_channel = int(os.getenv("PWM_CHANNEL", str(_infer_pwm_channel_from_physical_pin(pwm_pin_physical))))
        pwm_frequency_hz = int(os.getenv("PWM_FREQUENCY_HZ", "25000"))

        if pwm_frequency_hz <= 0:
            pwm_frequency_hz = 25000

        return AppConfig(
            data_dir=data_dir,
            log_level=log_level,
            pwm_pin_physical=pwm_pin_physical,
            pwm_chip=pwm_chip,
            pwm_channel=pwm_channel,
            pwm_frequency_hz=pwm_frequency_hz,
        )


def _infer_pwm_channel_from_physical_pin(physical_pin: int) -> int:
    # On Raspberry Pi, PWM channels are typically:
    # PWM0: GPIO12 (Pin 32) or GPIO18 (Pin 12)
    # PWM1: GPIO13 (Pin 33) or GPIO19 (Pin 35)
    # This function guesses the channel, but you should set PWM_CHIP/PWM_CHANNEL explicitly when in doubt.
    if physical_pin in (32, 12):
        return 0
    if physical_pin in (33, 35):
        return 1
    return 0