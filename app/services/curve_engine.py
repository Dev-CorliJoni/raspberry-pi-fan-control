# app/services/curve_engine.py
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class CurveEvaluationResult:
    duty_percent: int
    warnings: List[str]


class CurveEngine:
    def evaluate(self, points: List[Tuple[float, int]], temp_c: float) -> CurveEvaluationResult:
        warnings: List[str] = []
        if not points:
            return CurveEvaluationResult(duty_percent=0, warnings=["Curve has no points; using 0%"])

        pts = sorted([(float(t), int(d)) for t, d in points], key=lambda x: x[0])
        for t, d in pts:
            if d < 0 or d > 100:
                warnings.append("Curve contains duty outside 0..100; values will be clamped")

        # Clamp outside range
        if temp_c <= pts[0][0]:
            return CurveEvaluationResult(duty_percent=_clamp_duty(pts[0][1]), warnings=warnings)
        if temp_c >= pts[-1][0]:
            return CurveEvaluationResult(duty_percent=_clamp_duty(pts[-1][1]), warnings=warnings)

        # Linear interpolation between nearest points.
        for i in range(1, len(pts)):
            t0, d0 = pts[i - 1]
            t1, d1 = pts[i]
            if t0 <= temp_c <= t1:
                if t1 == t0:
                    return CurveEvaluationResult(duty_percent=_clamp_duty(d1), warnings=warnings)
                ratio = (temp_c - t0) / (t1 - t0)
                duty = float(d0) + ratio * (float(d1) - float(d0))
                return CurveEvaluationResult(duty_percent=_clamp_duty(int(round(duty))), warnings=warnings)

        return CurveEvaluationResult(duty_percent=_clamp_duty(pts[-1][1]), warnings=warnings)


def _clamp_duty(d: int) -> int:
    return max(0, min(100, int(d)))