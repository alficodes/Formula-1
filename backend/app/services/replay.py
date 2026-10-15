import asyncio, json, logging
from datetime import datetime, timezone
from typing import Any
from app.models.race import demo_state
from app.strategy.engine import simulate_strategies

log = logging.getLogger(__name__)
class ReplayService:
    def __init__(self):
        self.state = demo_state(); self.running = False; self._lock = asyncio.Lock(); self._subscribers: set[asyncio.Queue] = set()
        self.strategies = simulate_strategies(self.state.to_dict())
    def snapshot(self) -> dict[str, Any]:
        data = self.state.to_dict(); data["timestamp"] = datetime.now(timezone.utc).isoformat(); data["strategies"] = self.strategies
        data["recommendation"] = self.recommendation(); return data
    def recommendation(self) -> dict[str, Any]:
        best = self.strategies[0]
        # Domain guardrail: with active SC + rain in 4 laps, prefer flexible Hard unless rain is imminent.
        inter = next(x for x in self.strategies if x["id"] == "inter")
        if self.state.rain_eta_laps <= 2 and self.state.rain_probability >= .65: best = inter
        elif self.state.safety_car_active and self.state.rain_probability >= .65:
            hard = next(x for x in self.strategies if x["id"] == "hard")
            best = hard if hard["expected_remaining_seconds"] <= inter["expected_remaining_seconds"] + 5 else inter
        return {**best, "alternate": inter if best["id"] != "inter" else next(x for x in self.strategies if x["id"] == "hard"), "trigger_conditions": ["Pit for Intermediates if rain begins or probability exceeds 85% within 2 laps.", "Stay out only if Safety Car remains deployed and rainfall has not started.", "Reassess after every lap or any track-status change."]}
    async def publish(self, typ: str, payload: dict):
        msg = {"type": typ, "race_id": self.state.race_id, "lap": self.state.current_lap, "timestamp": datetime.now(timezone.utc).isoformat(), "payload": payload}
        for q in list(self._subscribers):
            try: q.put_nowait(msg)
            except asyncio.QueueFull: pass
    async def next_lap(self):
        async with self._lock:
            if self.state.current_lap >= self.state.total_laps:
                self.state.status = "FINISHED"; self.state.track_status = "CHEQUERED"
            else:
                self.state.current_lap += 1
                self.state.rain_eta_laps = max(0, self.state.rain_eta_laps - 1)
                self.state.rain_probability = min(.98, self.state.rain_probability + .035)
                if self.state.rain_eta_laps == 0:
                    self.state.rainfall_mm = max(.1, self.state.rainfall_mm + .2); self.state.track_status = "WET"; self.state.safety_car_active = False
                    self.state.alerts = ["Rain has reached the circuit", "Intermediate tire window active"]
                elif self.state.current_lap == 34:
                    self.state.alerts = ["Rain expected in 1 lap", "Pit window opening"]
                else: self.state.alerts = [f"Rain expected in {self.state.rain_eta_laps} laps" if self.state.rain_eta_laps else "Rain on track"]
                for d in self.state.drivers:
                    d.tire_age += 1; d.tire_wear = min(100, d.tire_wear + (1.4 if d.compound == "Medium" else .8)); d.fuel_kg = max(0, d.fuel_kg - 1.7)
                    d.lap_time += .03
                self.strategies = simulate_strategies(self.state.to_dict(), seed=self.state.current_lap)
            await self.publish("race_state", self.snapshot())
            await self.publish("weather", {"rain_probability": self.state.rain_probability, "rain_eta_laps": self.state.rain_eta_laps, "rainfall_mm": self.state.rainfall_mm, "track_temp_c": self.state.track_temp_c})
            await self.publish("strategy", {"rankings": self.strategies[:5]})
            await self.publish("recommendation", self.recommendation())
            if self.state.alerts: await self.publish("alert", {"alerts": self.state.alerts})
            return self.snapshot()
    async def reset(self):
        self.state = demo_state(); self.strategies = simulate_strategies(self.state.to_dict()); self.running = False
        await self.publish("race_state", self.snapshot()); return self.snapshot()

replay_service = ReplayService()
