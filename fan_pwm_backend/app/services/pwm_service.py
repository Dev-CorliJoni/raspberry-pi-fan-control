# app/services/pwm_service.py
import logging
import time

from app.hardware.pwm.sysfs_pwm_writer import SysfsPwmWriter

logger = logging.getLogger(__name__)


class PwmService:
    def __init__(self, pwm_chip: str, pwm_channel: int) -> None:
        self._writer = SysfsPwmWriter(pwm_chip=pwm_chip, pwm_channel=pwm_channel)
        self._last_set_duty: int = 0
        self._kickstart_active_until: float | None = None
        self._kickstart_target_duty: int | None = None

    def try_init(self, frequency_hz: int) -> None:
        # Initialize sysfs PWM. This can fail due to missing sysfs nodes or permissions.
        self._writer.ensure_exported()
        self._writer.set_frequency_hz(int(frequency_hz))
        self._writer.set_duty_percent(0)
        self._writer.enable()

    def set_duty(self, duty_percent: int, kickstart_enabled: bool, kickstart_duty: int, kickstart_ms: int) -> None:
        duty_percent = max(0, min(100, int(duty_percent)))

        now = time.time()
        if self._kickstart_active_until is not None:
            if now < self._kickstart_active_until:
                return
            # Kickstart window ended -> apply target
            if self._kickstart_target_duty is not None:
                self._writer.set_duty_percent(self._kickstart_target_duty)
                self._last_set_duty = self._kickstart_target_duty
            self._kickstart_active_until = None
            self._kickstart_target_duty = None
            return

        # Kickstart only when transitioning 0 -> >0
        if kickstart_enabled and self._last_set_duty == 0 and duty_percent > 0 and kickstart_ms > 0:
            self._writer.set_duty_percent(max(0, min(100, int(kickstart_duty))))
            self._kickstart_active_until = now + (float(kickstart_ms) / 1000.0)
            self._kickstart_target_duty = duty_percent
            return

        self._writer.set_duty_percent(duty_percent)
        self._last_set_duty = duty_percent

    def disable(self) -> None:
        try:
            self._writer.disable()
        except Exception:
            logger.exception("Failed to disable PWM")