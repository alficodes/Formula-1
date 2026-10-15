# F1 Pit Strategist

A runnable Monaco-specific Formula 1 pit-strategy prototype. The default Lap 31 demo scenario starts P3 on 18-lap-old Mediums at 72% wear, with a Safety Car active and rain forecast within four laps. The dashboard compares 12 candidate strategies using Monte Carlo uncertainty sampling, streams state over WebSockets, and provides a transparent recommendation with trigger conditions.

> **Prototype/data note:** the seeded Lap 31 scenario is a designed strategy exercise, not a claim that these values reproduce the actual 2024 Monaco race at that exact lap. FastF1 historical ingestion is available as an optional loader; the demo mode is deterministic and works without downloading race data. Current live telemetry is not guaranteed. Simulation outputs are estimates, not race-engineering advice.

## Architecture

- `backend/`: FastAPI REST/WebSocket API, race state, FastF1 loader, tire/lap models, Monte Carlo strategy engine and pytest suite.
- `backend/prisma/schema.prisma`: PostgreSQL schema covering circuits, teams, drivers, race state, tires/stints, pit stops, weather, race control, telemetry, strategies, simulations and recommendations.
- `backend/prisma/seed.py`: reference seed for five teams, ten drivers, five compounds and the Monaco Lap 31 scenario.
- `frontend/`: React + TypeScript + Vite + Recharts responsive dark race-control dashboard.
- `docker-compose.yml`: API, frontend, PostgreSQL/TimescaleDB and Redis.

The API is intentionally resilient in demo mode: state runs in process so the complete replay works without external services. Redis/PostgreSQL are provisioned in Compose for the persistence integration path; the prototype currently does not claim that every request is persisted to those services.

## Quick start (local)

Requirements: Python 3.11+, Node.js 20+, npm.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open Swagger at `http://localhost:8000/docs` and health at `http://localhost:8000/health`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Docker Compose

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Dashboard: `http://localhost:5173`
- API / Swagger: `http://localhost:8000/docs`
- PostgreSQL/TimescaleDB: `localhost:5432` (`f1` / `f1password` / `f1pit`)
- Redis: `localhost:6379`

For a production deployment, change default credentials, restrict CORS, use TLS, and configure secrets through the deployment environment rather than `.env` files.

## Database / Prisma

The schema uses Prisma's Python client generator. With the services running and `DATABASE_URL` set:

```bash
cd backend
prisma db push --schema prisma/schema.prisma
python prisma/seed.py
```

The TimescaleDB extension is available in the database image; hypertable conversion is intentionally not automatic because the current schema uses Prisma-managed relational tables. If converting telemetry/state tables to hypertables, do so with a reviewed SQL migration and ensure unique constraints comply with TimescaleDB's time-partition rules.

## Tests and build

```bash
# Backend
cd backend
pytest -q

# Frontend
cd frontend
npm install
npm test
npm run build
```

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/version` | Version and demo-mode status |
| GET | `/api/v1/monaco/state` | Current state, ranked strategies and recommendation |
| GET | `/api/v1/monaco/drivers` | Driver list |
| GET | `/api/v1/monaco/drivers/{driver_id}` | Driver detail |
| GET | `/api/v1/monaco/laps/{lap_number}` | Available lap snapshot |
| GET | `/api/v1/monaco/positions` | Classification |
| GET | `/api/v1/monaco/track-status` | Track / Safety Car status |
| GET | `/api/v1/monaco/weather` | Weather state and rain ETA |
| GET | `/api/v1/monaco/pit-window` | Pit window assessment |
| GET | `/api/v1/monaco/strategies` | Ranked strategies |
| POST | `/api/v1/monaco/simulate` | Re-run simulation (body supports iterations, rain probability/ETA and Safety Car state) |
| POST | `/api/v1/monaco/replay/next-lap` | Advance one lap |
| POST | `/api/v1/monaco/replay/start` | Mark replay running |
| POST | `/api/v1/monaco/replay/pause` | Pause autoplay marker |
| POST | `/api/v1/monaco/replay/reset` | Reset to Lap 31 scenario |
| GET | `/api/v1/monaco/recommendation` | Best strategy, alternate and trigger conditions |
| WS | `/ws/monaco/replay/{race_id}` | Live replay event stream |

Simulation request example:

```json
{"iterations": 500, "rain_probability": 0.78, "rain_eta_laps": 3, "safety_car_active": true}
```

WebSocket events use this envelope:

```json
{"type":"race_state","race_id":"monaco-2024","lap":31,"timestamp":"ISO-8601","payload":{}}
```

Event types include `race_state`, `weather`, `strategy`, `alert`, and `recommendation`. Connect with `ws://localhost:8000/ws/monaco/replay/monaco-2024`, then POST to `/api/v1/monaco/replay/next-lap` to generate events.

## Strategy model

The simulator evaluates stay out, pit now, pit next lap, Soft, Medium, Hard, Intermediate, Wet, one-stop, two-stop, undercut and overcut. Every strategy runs at least 500 Monte Carlo trials with uncertainty in rain timing/probability, Safety Car continuation, pit loss, lap-time noise and traffic. Results include projected remaining time, expected position, tire/weather/Safety Car/traffic risks, gain/loss probabilities, confidence and a natural-language explanation.

Monaco-specific heuristics prioritize track position because overtaking is difficult; pit loss is modeled at about 22 seconds under green and 12.5 seconds under Safety Car. A rain forecast increases the value of a flexible compound and can trigger an Intermediate recommendation when rain is imminent. These are illustrative model assumptions and should be calibrated against historical lap data before real use.

## FastF1 historical replay

`backend/app/replay/fastf1_loader.py` loads a Monaco race session and caches it under `.fastf1-cache`. It handles unavailable downloads/fields by returning `None`, allowing demo mode to continue. To keep the prototype reliable offline, the dashboard defaults to the explicitly defined Lap 31 scenario; mapping full FastF1 telemetry into replay snapshots is an extension point rather than a pretense that the demo values are historical telemetry.
