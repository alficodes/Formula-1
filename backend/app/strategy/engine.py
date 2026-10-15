import random, statistics
from .models import COMPOUNDS, PIT_LOSS_GREEN, PIT_LOSS_SC, StrategyResult

STRATEGIES = [
    ("stay-out", "Stay out", "stay", "Medium"), ("pit-now", "Pit now", "pit", "Medium"),
    ("pit-next", "Pit next lap", "pit_next", "Medium"), ("soft", "Pit for Soft", "pit", "Soft"),
    ("medium", "Pit for Medium", "pit", "Medium"), ("hard", "Pit for Hard", "pit", "Hard"),
    ("inter", "Pit for Intermediates", "pit", "Intermediate"), ("wet", "Pit for Wet", "pit", "Wet"),
    ("one-stop", "One-stop plan", "one_stop", "Hard"), ("two-stop", "Two-stop plan", "two_stop", "Soft"),
    ("undercut", "Undercut attempt", "undercut", "Medium"), ("overcut", "Overcut attempt", "overcut", "Medium"),
]

def tire_wear(compound: str, age: int, track_temp: float = 31.5, driving_style: float = 1.0, circuit_factor: float = 1.18) -> float:
    base = COMPOUNDS[compound]["wear"]
    return min(100.0, max(0.0, age * base * 2.15 * driving_style * circuit_factor * (1 + max(0, track_temp - 25) * .003)))

def lap_delta(compound: str, age: int, rain_probability: float = 0.0) -> float:
    data = COMPOUNDS[compound]
    dry_penalty = data["pace"] + max(0, age - 5) ** 1.35 * 0.035 * data["wear"]
    wet_penalty = (1 - rain_probability) * (data["wet"] if compound in ("Intermediate", "Wet") else 0) + rain_probability * (data["wet"] if compound not in ("Intermediate", "Wet") else 0)
    cliff = max(0, age - 18) ** 2 * 0.045
    return dry_penalty + wet_penalty + cliff

def simulate_strategies(state: dict, iterations: int = 500, seed: int = 31) -> list[dict]:
    rng = random.Random(seed)
    current = next(d for d in state["drivers"] if d["driver_id"] == state["our_driver_id"])
    remaining = state["total_laps"] - state["current_lap"]
    results = []
    for sid, name, action, tire in STRATEGIES:
        totals, positions = [], []
        weather_failures, traffic_events, worn_finishes = 0, 0, 0
        for _ in range(max(500, iterations)):
            rain_eta = max(0, state["rain_eta_laps"] + rng.choice([-2, -1, 0, 1, 2]))
            rain_prob = min(1, max(0, state["rain_probability"] + rng.gauss(0, .12)))
            sc_active = state["safety_car_active"] and rng.random() < .72
            pit_loss = PIT_LOSS_SC if sc_active else PIT_LOSS_GREEN
            stop = action in ("pit", "pit_next", "undercut", "two_stop", "one_stop")
            pit_lap_delay = 1 if action == "pit_next" else 0
            start_age = 0 if stop else current["tire_age"]
            compound = tire if stop else current["compound"]
            total = 0.0
            rain_start = max(0, rain_eta + rng.randint(-1, 1))
            caught_on_slicks = False
            for i in range(1, remaining + 1):
                age = start_age + i + pit_lap_delay
                rain_intensity = min(1.0, max(0.0, (i - rain_start + 1) * .24)) if i >= rain_start else 0.0
                wet = min(1.0, rain_prob * rain_intensity)
                active_compound = compound
                # A single-stop plan can switch to intermediates once rain wets the track.
                if tire in ("Intermediate", "Wet") and rain_intensity < .35:
                    active_compound = "Hard" if tire == "Intermediate" else "Medium"
                elif tire not in ("Intermediate", "Wet") and rain_intensity > .58:
                    caught_on_slicks = True
                base = 75.6 + lap_delta(active_compound, age, wet)
                if i == 1 and stop: total += pit_loss + rng.gauss(0, 1.25)
                if action == "two_stop" and i == max(2, round(remaining * .55)):
                    total += (PIT_LOSS_SC if sc_active and i < 4 else PIT_LOSS_GREEN) * .75
                if action == "undercut" and i <= 2: total -= 0.45
                if action == "overcut" and i <= 2: total -= 0.12
                if age > 22 and active_compound not in ("Wet", "Intermediate"):
                    worn_finishes += 1 if i == remaining else 0
                total += base + rng.gauss(0, .19 + (0.08 if age > 20 else 0))
            # Rainfall timing produces a nonlinear crossover; surface-water uncertainty is sampled.
            if tire == "Intermediate" and rain_start > 4: total += rng.uniform(4, 15)
            if tire == "Wet" and rain_start > 3: total += rng.uniform(9, 25)
            if tire not in ("Intermediate", "Wet") and rain_start <= 2: total += rng.triangular(5, 24, 12)
            if caught_on_slicks:
                weather_failures += 1
                total += rng.triangular(8, 32, 16)
            elif tire in ("Intermediate", "Wet") and rain_start > 4:
                weather_failures += .2
            traffic = rng.triangular(0, 5.5, 1.0) if stop else rng.triangular(0, 2.5, .4)
            traffic_events += traffic > 1.5
            total += traffic
            totals.append(total)
            # Use the local gaps as a rough traffic envelope; Monaco makes passes rare.
            gap_ahead = max(0.8, float(current.get("gap_ahead", 2.0)))
            gap_behind = max(1.0, float(current.get("gap_behind", 3.0)))
            position_delta = 0
            if total < (75.6 * remaining - gap_ahead * 1.2) and rng.random() < .38: position_delta -= 1
            if total > (75.6 * remaining + gap_behind * 1.5) and rng.random() < .34: position_delta += 1
            if action == "undercut" and rng.random() < .24: position_delta -= 1
            positions.append(max(1, min(20, 3 + position_delta + rng.choice([0,0,0,1,-1]))))
        avg = statistics.mean(totals)
        gain = min(.92, max(.04, .5 + (statistics.mean(positions) - 3) * -.16 + rng.uniform(-.05, .05)))
        wear_risk = min(1, max(0, (current["tire_wear"] + (remaining * (1.25 if compound == "Medium" else .78) if not stop else remaining * .28) - 78) / 45))
        weather_risk = min(1, max(0, weather_failures / max(1, iterations)))
        sc_risk = min(1, max(0, .25 + (0.2 if state["safety_car_active"] and not stop else 0) + (0.2 if stop and not state["safety_car_active"] else 0)))
        traffic_risk = min(1, traffic_events / max(1, iterations))
        confidence = max(52, min(94, 91 - (statistics.pstdev(totals) / 3) - weather_risk * 10))
        results.append(StrategyResult(sid, name, action, tire, round(avg, 1), round(statistics.mean(positions), 2), round(3-statistics.mean(positions), 2), round(wear_risk*100, 1), round(weather_risk*100, 1), round(sc_risk*100, 1), round(traffic_risk*100, 1), round(gain, 2), round(1-gain, 2), round(confidence, 1), _explain(sid, tire, rain_prob, sc_active)).to_dict())
    results.sort(key=lambda x: (x["expected_remaining_seconds"] + x["expected_position"] * 8 + x["weather_risk"] * .08))
    for idx, item in enumerate(results): item["rank"] = idx + 1
    return results

def _explain(sid: str, tire: str, rain: float, sc: bool) -> str:
    if sid == "inter": return "Rain is likely soon; intermediates reduce the risk of losing multiple seconds when the track becomes damp. Monitor rainfall before committing."
    if sid == "hard": return "Hard tires offer the safest dry-to-damp bridge and can cover the remaining distance, but may be slow if rain arrives heavily."
    if sid == "stay-out": return "Track position is valuable at Monaco, and the Safety Car reduces immediate pace pressure; however, the worn Mediums are a growing liability."
    if sid == "undercut": return "Fresh tires can create an undercut, but Monaco traffic and limited overtaking make a clear out-lap essential."
    if sid == "overcut": return "Staying out can preserve track position and avoid traffic, but the worn tire and approaching rain narrow the window."
    if sid == "pit-now": return "The Safety Car makes this a relatively cheap stop. Choose the compound based on the rain radar and avoid being caught on slicks in a wet sector."
    return f"This plan targets {tire} performance. Rain uncertainty and Monaco's low-overtaking circuit mean track position and pit timing remain critical."
