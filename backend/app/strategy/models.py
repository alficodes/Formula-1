from dataclasses import dataclass, asdict
from typing import Any

COMPOUNDS = {"Soft": {"pace": -0.35, "wear": 1.55, "wet": 1.7}, "Medium": {"pace": 0.0, "wear": 1.0, "wet": 1.4}, "Hard": {"pace": 0.28, "wear": 0.68, "wet": 1.25}, "Intermediate": {"pace": 1.3, "wear": 0.9, "wet": 0.35}, "Wet": {"pace": 3.8, "wear": 0.85, "wet": 0.15}}
PIT_LOSS_GREEN = 22.0
PIT_LOSS_SC = 12.5

@dataclass
class StrategyResult:
    id: str
    name: str
    action: str
    tire: str
    expected_remaining_seconds: float
    expected_position: float
    position_change: float
    tire_life_risk: float
    weather_risk: float
    safety_car_risk: float
    traffic_risk: float
    gain_probability: float
    loss_probability: float
    confidence: float
    explanation: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)
