# app/services/safety_service.py
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    duty_percent: int
    reason: str | None


class SafetyService:
    def apply(self, target_duty: int, max_temp_c: float | None, hard_limit_c: float, margin_c: float) -> SafetyDecision:
        # Safety rules:
        # - If max temp is unknown -> fail-safe 100%.
        # - If max temp >= (hard_limit - margin) -> 100%.
        if max_temp_c is None:
            return SafetyDecision(duty_percent=100, reason="temperature_unavailable_fail_safe")

        threshold = max(0.0, float(hard_limit_c) - float(margin_c))
        if max_temp_c >= threshold:
            return SafetyDecision(duty_percent=100, reason=f"hard_limit_preempt ({max_temp_c:.1f}C >= {threshold:.1f}C)")

        return SafetyDecision(duty_percent=int(target_duty), reason=None)