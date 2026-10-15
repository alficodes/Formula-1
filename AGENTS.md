# Repository guide for agents and contributors

## Conventions
- Python: 3.11+, type-aware functions, small modules, Pydantic at API boundaries, pytest Arrange–Act–Assert.
- TypeScript: strict mode, functional React components, API calls centralized in `src/services/api.ts` and API contracts in `src/types/`.
- Keep the API under `/api/v1`; do not rename response fields without updating frontend types/tests.
- Do not represent demo data as actual historical or live telemetry. Label assumptions and simulation output clearly.
- Log ingestion failures and degrade to demo mode if FastF1 cannot download data.
- Do not commit credentials, cache data, `node_modules`, `.venv`, or build output.

## Folder map
- `backend/app/main.py`: REST and WebSocket entry points.
- `backend/app/models/`: typed race-state dataclasses.
- `backend/app/services/replay.py`: replay lifecycle, state updates and event fanout.
- `backend/app/strategy/`: tire/lap-time model and Monte Carlo candidate scoring.
- `backend/app/replay/fastf1_loader.py`: optional historical session loader.
- `backend/app/tests/`: backend unit tests.
- `backend/prisma/schema.prisma`: relational data model.
- `backend/prisma/seed.py`: Prisma seed routine.
- `frontend/src/pages/Dashboard.tsx`: dashboard composition and replay controls.
- `frontend/src/components/`: reusable dashboard panels and strategy ranking.
- `frontend/src/tests/`: frontend tests.

## Commands
- API: `cd backend && uvicorn app.main:app --reload --port 8000`
- Backend tests: `cd backend && pytest -q`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Frontend tests/build: `cd frontend && npm test && npm run build`
- Full stack: `cp backend/.env.example backend/.env && docker compose up --build`
- Prisma: `cd backend && prisma db push --schema prisma/schema.prisma && python prisma/seed.py`

## Monaco strategy rules
- Scenario starts Lap 31/53, P3, 18-lap Mediums, 72% wear, Safety Car active and rain forecast within four laps.
- Compare all 12 strategies: stay out, pit now, pit next lap, Soft, Medium, Hard, Intermediates, Wet, one-stop, two-stop, undercut and overcut.
- Use at least 500 trials per simulation; include weather timing, pit-loss uncertainty, tire degradation and traffic noise.
- Track position has additional value at Monaco because overtaking is difficult.
- Safety Car pit loss is modeled lower than green-flag pit loss; do not imply exact values are universal.
- Recommendation must include alternate plan and explicit trigger conditions.

## Definition of done
- Backend starts and `/health`, `/docs` respond.
- All REST routes and WebSocket event envelope are exercised.
- Lap 31 scenario is visible in the dashboard and replay can advance/reset.
- All strategy candidates rank with risk/confidence fields and one recommendation is returned.
- Backend tests pass; frontend tests and production build pass.
- Compose config includes API, UI, Redis and TimescaleDB; setup steps and known prototype limitations are documented.
