# Backend

FastAPI service serving flight, airport, delay-stats, and cascade-link data to the web dashboard.

**Status**: built, tested, currently runs locally. Previously deployed live on Railway (serverless mode) from early development through August 2026 — see the root `README.md`'s "Deployment history" section for what happened and why it's local-only now.

## Contents
- `main.py` — app entrypoint, CORS config, `/health`
- `database.py` — SQLAlchemy session setup
- `schemas.py` — Pydantic response models
- `routers/flights.py` — all flight, airport, stats, and cascade endpoints

## Endpoints

- `GET /health` — service health check
- `GET /flights` — list flights with optional filters
- `GET /flights/physical` — physical (de-duplicated) flights, collapsing
  codeshare records that refer to the same underlying flight
- `GET /flights/{flight_id}` — single flight detail
- `GET /stats/delays` — aggregate delay statistics
- `GET /cascade/stats` — live cascade-link candidate count, using the same
  matching logic as `ml/cascade_link_diagnostic.py` (same aircraft,
  arrival→departure at the same airport, plausible turnaround window)
- `GET /airports` — list tracked airports

## Deployment notes (historical — Railway, retired)

When this was deployed on Railway, the setup was:
- Service `amusing-grace`, with Root Directory set to `backend` and start
  command `uvicorn main:app --host 0.0.0.0 --port $PORT`
- `DATABASE_URL` set via Railway's cross-service reference
  (`${{Postgres.DATABASE_URL}}`), never hardcoded, so it stayed in sync if
  the database connection details changed
- CORS scoped to the dashboard's stable production domain
  (`https://airline-delay-intelligence.vercel.app`) — not any
  per-deployment Vercel preview URL, since those change on every redeploy

This is kept here for reference in case the project is redeployed in the
future; it does not reflect the current running setup.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in local DATABASE_URL
uvicorn main:app --reload
```