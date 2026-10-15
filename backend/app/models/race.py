from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class DriverState:
    driver_id: str
    name: str
    team: str
    position: int
    gap_ahead: float
    gap_behind: float
    compound: str
    tire_age: int
    tire_wear: float
    fuel_kg: float
    pit_stops: int = 1
    lap_time: float = 75.0
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class RaceState:
    race_id: str = "monaco-2024"
    circuit: str = "Circuit de Monaco"
    current_lap: int = 31
    total_laps: int = 53
    status: str = "RUNNING"
    track_status: str = "SAFETY_CAR"
    safety_car_active: bool = True
    rain_probability: float = 0.78
    rain_eta_laps: int = 3
    rainfall_mm: float = 0.0
    track_temp_c: float = 31.5
    air_temp_c: float = 24.0
    our_driver_id: str = "NOR"
    drivers: list[DriverState] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "drivers": [d.to_dict() for d in self.drivers]}

def demo_state() -> RaceState:
    return RaceState(drivers=[
        DriverState("LEC", "Charles Leclerc", "Ferrari", 1, 0, 1.8, "Hard", 11, 48, 21.2, 1, 75.1),
        DriverState("PIA", "Oscar Piastri", "McLaren", 2, 1.4, 2.1, "Hard", 12, 51, 20.8, 1, 75.2),
        DriverState("NOR", "Lando Norris", "McLaren", 3, 2.1, 4.7, "Medium", 18, 72, 20.4, 1, 75.8),
        DriverState("SAI", "Carlos Sainz", "Ferrari", 4, 4.7, 2.2, "Medium", 15, 61, 20.1, 1, 75.6),
        DriverState("RUS", "George Russell", "Mercedes", 5, 2.2, 3.1, "Hard", 17, 58, 19.8, 1, 75.7),
        DriverState("HAM", "Lewis Hamilton", "Mercedes", 6, 3.1, 1.6, "Medium", 16, 63, 19.5, 1, 75.9),
        DriverState("VER", "Max Verstappen", "Red Bull", 7, 1.6, 2.8, "Hard", 19, 66, 19.2, 1, 75.5),
        DriverState("PER", "Sergio Perez", "Red Bull", 8, 2.8, 3.0, "Medium", 14, 56, 18.9, 1, 75.8),
        DriverState("ALO", "Fernando Alonso", "Aston Martin", 9, 3.0, 1.7, "Hard", 20, 69, 18.6, 1, 76.1),
        DriverState("STR", "Lance Stroll", "Aston Martin", 10, 1.7, 2.4, "Medium", 13, 53, 18.3, 1, 76.0),
    ], alerts=["SAFETY CAR deployed", "Rain expected in 3 laps", "Medium tire life approaching critical range"])
