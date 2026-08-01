# Backend

FastAPI service serving flight, airport, and delay-stats data to the web dashboard.

**Live**: https://amusing-grace-production-54d1.up.railway.app
**Status**: built, tested, and deployed live on Railway (serverless mode — scales
to zero when idle, so the first request after inactivity may take a few
seconds to cold-start).

## Contents
- `main.py` — app entrypoint, CORS config, `/health`
- `database.py` — SQLAlchemy session setup
- `schemas.py` — Pydantic response models
- `routers/flights.py` — all flight, airport, and stats endpoints

## Endpoints

- `GET /health` — service health check
- `GET /flights` — list flights with optional filters
- `GET /flights/physical` — physical (de-duplicated) flights, collapsing
  codeshare records that refer to the same underlying flight
- `GET /flights/{flight_id}` — single flight detail
- `GET /stats/delays` — aggregate delay statistics
- `GET /airports` — list tracked airports

## Deployment notes

- Deployed on Railway as service `amusing-grace`, with Root Directory set to
  `backend` and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- `DATABASE_URL` is set via Railway's cross-service reference
  (`${{Postgres.DATABASE_URL}}`), never hardcoded, so it stays in sync if the
  database connection details change.
- CORS is scoped to the dashboard's stable production domain
  (`https://airline-delay-intelligence.vercel.app`) — not any per-deployment
  Vercel preview URL, since those change on every redeploy.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL
uvicorn main:app --reload
```