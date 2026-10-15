import asyncio, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import settings
from app.services.replay import replay_service
from app.strategy.engine import simulate_strategies

logging.basicConfig(level=logging.INFO)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("f1pit").info("F1 Pit Strategist starting; demo mode=%s", settings.demo_mode)
    yield
app = FastAPI(title="F1 Pit Strategist API", version="1.0.0", description="Monaco race replay and Monte Carlo pit strategy prototype", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class SimulateRequest(BaseModel):
    iterations: int = Field(default=500, ge=500, le=10000)
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_eta_laps: int | None = Field(default=None, ge=0, le=20)
    safety_car_active: bool | None = None

@app.get("/health")
def health(): return {"status": "ok", "service": "f1-pit-strategist"}
@app.get("/version")
def version(): return {"version": app.version, "api": "v1", "demo_mode": settings.demo_mode}
@app.get("/api/v1/monaco/state")
def state(): return replay_service.snapshot()
@app.get("/api/v1/monaco/drivers")
def drivers(): return replay_service.state.to_dict()["drivers"]
@app.get("/api/v1/monaco/drivers/{driver_id}")
def driver(driver_id: str):
    d = next((d for d in replay_service.state.drivers if d.driver_id.lower() == driver_id.lower()), None)
    if not d: raise HTTPException(404, "Driver not found")
    return d.to_dict()
@app.get("/api/v1/monaco/laps/{lap_number}")
def lap(lap_number: int):
    if lap_number < 1 or lap_number > replay_service.state.current_lap: raise HTTPException(404, "Lap not available in current replay history")
    s = replay_service.snapshot(); return {"lap": lap_number, "race_id": s["race_id"], "track_status": s["track_status"], "weather": {"rain_probability": s["rain_probability"], "rainfall_mm": s["rainfall_mm"]}, "positions": [{"driver_id": d["driver_id"], "position": d["position"], "lap_time": d["lap_time"]} for d in s["drivers"]]}
@app.get("/api/v1/monaco/positions")
def positions(): return sorted(replay_service.state.to_dict()["drivers"], key=lambda d: d["position"])
@app.get("/api/v1/monaco/track-status")
def track_status(): return {"status": replay_service.state.track_status, "safety_car_active": replay_service.state.safety_car_active, "lap": replay_service.state.current_lap}
@app.get("/api/v1/monaco/weather")
def weather():
    s = replay_service.state; return {"rain_probability": s.rain_probability, "rain_eta_laps": s.rain_eta_laps, "rainfall_mm": s.rainfall_mm, "track_temp_c": s.track_temp_c, "air_temp_c": s.air_temp_c}
@app.get("/api/v1/monaco/pit-window")
def pit_window():
    s = replay_service.state; return {"open": s.safety_car_active or s.rain_eta_laps <= 3, "recommended_window": [s.current_lap, min(s.total_laps, s.current_lap + max(1, s.rain_eta_laps))], "reason": "Safety Car reduces pit loss; rain forecast compresses the slick-to-intermediate decision window."}
@app.get("/api/v1/monaco/strategies")
def strategies(): return replay_service.strategies
@app.post("/api/v1/monaco/simulate")
def simulate(req: SimulateRequest):
    s = replay_service.state.to_dict()
    if req.rain_probability is not None: s["rain_probability"] = req.rain_probability
    if req.rain_eta_laps is not None: s["rain_eta_laps"] = req.rain_eta_laps
    if req.safety_car_active is not None: s["safety_car_active"] = req.safety_car_active
    return {"iterations": req.iterations, "strategies": simulate_strategies(s, req.iterations)}
@app.post("/api/v1/monaco/replay/next-lap")
async def next_lap(): return await replay_service.next_lap()
@app.post("/api/v1/monaco/replay/start")
async def start_replay():
    replay_service.running = True
    return {"running": True, "message": "Use the WebSocket stream or next-lap endpoint to advance the demo replay."}
@app.post("/api/v1/monaco/replay/pause")
async def pause_replay(): replay_service.running = False; return {"running": False}
@app.post("/api/v1/monaco/replay/reset")
async def reset_replay(): return await replay_service.reset()
@app.get("/api/v1/monaco/recommendation")
def recommendation(): return replay_service.recommendation()
@app.websocket("/ws/monaco/replay/{race_id}")
async def replay_ws(websocket: WebSocket, race_id: str):
    await websocket.accept(); q: asyncio.Queue = asyncio.Queue(maxsize=20); replay_service._subscribers.add(q)
    try:
        await websocket.send_json({"type": "race_state", "race_id": race_id, "lap": replay_service.state.current_lap, "timestamp": replay_service.snapshot()["timestamp"], "payload": replay_service.snapshot()})
        while True: await websocket.send_json(await q.get())
    except WebSocketDisconnect: pass
    finally: replay_service._subscribers.discard(q)
