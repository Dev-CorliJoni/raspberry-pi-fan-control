# app/core/units.py
from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSystem:
    # Display and input unit. Internally we use Celsius.
    name: str  # "C" | "F" | "K"


def c_to_display(c: float, unit: str) -> float:
    u = (unit or "C").upper()
    if u == "F":
        return c * 9.0 / 5.0 + 32.0
    if u == "K":
        return c + 273.15
    return c


def display_to_c(v: float, unit: str) -> float:
    u = (unit or "C").upper()
    if u == "F":
        return (v - 32.0) * 5.0 / 9.0
    if u == "K":
        return v - 273.15
    return v