"""Crowd risk engine: density + growth trend -> risk level and action."""
from dataclasses import dataclass

# People per square metre. Thresholds follow common crowd-safety guidance
# (about 4+/m2 is dangerous, 5+/m2 is critical). Tune with field data.
LEVELS = [(2.0, "SAFE"), (4.0, "MODERATE"), (5.0, "HIGH"), (float("inf"), "CRITICAL")]

ACTIONS = {
    "SAFE": "Normal monitoring.",
    "MODERATE": "Increase patrol; keep exits clear.",
    "HIGH": "Meter entry, open alternate routes, alert control room.",
    "CRITICAL": "Stop inflow, divert crowd, dispatch rescue and medical teams.",
}
ORDER = ["SAFE", "MODERATE", "HIGH", "CRITICAL"]


@dataclass
class ZoneReading:
    zone: str
    count: int
    area_m2: float
    prev_count: int = 0  # count from previous interval (e.g. 5 min ago)


@dataclass
class RiskResult:
    zone: str
    density: float
    growth_pct: float
    level: str
    action: str


def density(count: int, area_m2: float) -> float:
    if area_m2 <= 0:
        raise ValueError("area_m2 must be positive")
    return count / area_m2


def classify_density(d: float) -> str:
    for limit, name in LEVELS:
        if d < limit:
            return name
    return "CRITICAL"


def assess(reading: ZoneReading) -> RiskResult:
    d = density(reading.count, reading.area_m2)
    level = classify_density(d)
    growth = 0.0
    if reading.prev_count > 0:
        growth = (reading.count - reading.prev_count) / reading.prev_count * 100
    # Rapid inflow (>20% per interval) escalates risk one level.
    if growth > 20 and level != "CRITICAL":
        level = ORDER[ORDER.index(level) + 1]
    return RiskResult(reading.zone, round(d, 2), round(growth, 1), level, ACTIONS[level])
