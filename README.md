# Airline Delay Intelligence (SkyPulse)

AI-powered flight delay prediction and disruption cascade analytics platform, built on real-time flight and weather data, focused on Doha Hamad International (DOH) and Qatar Airways.

**Live dashboard**: https://airline-delay-intelligence.vercel.app
**Backend**: not currently deployed live — see [Deployment history](#deployment-history) below. Fully runnable locally in ~10 minutes; see Setup.

## Problem

Flight delays are one of the largest cost and customer-experience drivers in airline operations. A single delayed inbound aircraft can cascade into delays across its next several scheduled legs if turnaround buffers aren't enough to absorb the loss of time. This project predicts individual flight delays and estimates how those delays propagate downstream through an aircraft's rotation — the kind of analysis airline ops control centers rely on.

## Architecture

```
                    EXTERNAL APIs
        (AviationStack, OpenWeatherMap, AeroDataBox)
                          |
                          v
        SCHEDULED INGESTION SERVICE
        (polls daily, quota-aware)
        runs locally via ingestion/scheduler.py
                          |
                          v
                  POSTGRESQL
        (flights, weather, predictions, cascade links)
              runs locally
                          |
                          v
                  ML LAYER
        (delay classifier, delay regressor,
         cascade-link diagnostic -- all built and
         run against real data; cascade model and
         seasonal forecasting blocked on data volume)
                          |
                          v
                FASTAPI BACKEND
        runs locally (uvicorn main:app --reload)
                          |
            +-------------+-------------+
            |                           |
            v                           v
    REACT DASHBOARD              FLUTTER MOBILE APP
    (ops view)                   (traveler-facing alerts)
    5 pages: Overview, Live Flights,
    Delay Stats, Cascade Risk, Airports --
    all built and working against locally-run
    backend data.
```

## Tech stack

- **Ingestion**: Python, AviationStack API, OpenWeatherMap API — runs locally
- **Database**: PostgreSQL — runs locally
- **ML**: scikit-learn (classifier, regressor), pandas/SQL (cascade-link diagnostic). Prophet for forecasting — not yet started.
- **Backend**: FastAPI — runs locally
- **Web dashboard**: React + Vite — deployed on Vercel (frontend only; see Deployment history for why the backend isn't currently live)
- **Mobile app**: Flutter
- **Deployment**: see Deployment history below

## Deployment history

This project was deployed live end-to-end (Railway for ingestion, database, and backend; Vercel for the dashboard) from early development through August 2026. Railway's trial credit was exhausted while the project was on a short break, and rather than take on a recurring hosting cost for a portfolio project, development moved to a fully local setup: local Postgres, local ingestion scheduler, local FastAPI backend.

The Vercel-hosted dashboard above reflects the frontend only — the earlier Railway backend it originally pointed to is no longer running, so live data won't load there. The system is fully functional and demonstrable locally; see Setup below to run it end-to-end in about 10 minutes.

## Status

This project is being built incrementally with real commit history, not uploaded as a finished product. Current progress:

- [x] Ingestion service — built, tested, runs locally on a daily polling schedule
- [x] Database schema — TIMESTAMPTZ timezone handling, indexes, data-quality constraints
- [x] Airport enrichment — all tracked airports have real name/city/country/coordinates (OurAirports)
- [x] Initial exploratory data analysis — data health checks, codeshare de-duplication, delay distribution
- [x] FastAPI backend — built, tested, runs locally
- [x] React dashboard — Overview, Live Flights, Delay Stats, Cascade Risk, and Airports all built and tested against a locally-run backend
- [x] Cascade Risk dashboard page — live-updating (`GET /cascade/stats`), correctly reports 0 candidate pairs found so far, with the structural reason documented (see `ml/README.md`)
- [x] Delay classification + regression models — built, run against real data, results honestly documented as pipeline-validation checkpoints (small sample size), not production-ready predictions
- [ ] Cascade propagation model — blocked on cascade-link candidate volume (structural DOH-only-tracking limitation, documented in `ml/README.md`)
- [ ] Seasonal delay forecasting
- [ ] Flutter mobile app
- [ ] Docker Compose deployment + demo

## Repository structure

| Folder | Purpose |
|---|---|
| `ingestion/` | Scheduled API polling service |
| `database/` | PostgreSQL schema and migrations |
| `scripts/` | One-off utility scripts (e.g. airport enrichment) |
| `notebooks/` | EDA and model development notebooks |
| `ml/` | Training scripts and model artifacts |
| `backend/` | FastAPI service |
| `web-dashboard/` | React ops dashboard |
| `mobile-app/` | Flutter traveler-facing app |

## Known data characteristics

Documented in detail in `ingestion/README.md`:
- **Codeshare duplication** — AviationStack returns each codeshare as a separate flight record, even when multiple flight numbers refer to the same physical flight. Handled via de-duplication logic in the EDA notebook.
- **Timezone handling** — AviationStack mislabels local timestamps with a UTC designator; ingestion re-localizes using the API's separate `timezone` field before converting to true UTC. All timestamp columns use `TIMESTAMPTZ`.

## Known Limitations

**AviationStack free-tier data quality**: The free tier has occasional stale schedules and incomplete fields. Delay values outside plausible bounds (< -60 min or > 720 min) are excluded from analysis, with counts logged transparently rather than silently dropped.

**Codeshare partners**: Some flights list airlines that appear unusual at first glance (e.g. regional or long-haul carriers as partners on Doha routes). These have been cross-checked against Hamad International Airport's own published schedules and confirmed as legitimate codeshare arrangements, not data errors.

**API quota constraints**: The free AviationStack tier is capped at 100 requests/month. Ingestion is scoped to poll once daily for a single tracked airport (DOH) to stay well within budget.

**Cascade modeling data volume**: `ml/cascade_link_diagnostic.py` finds 0 valid same-aircraft arrival→departure pairs across multiple independent data collection periods (both the original Railway-hosted dataset and the current local rebuild). This is a structural consequence of tracking only DOH — see `ml/README.md` for the full explanation.

## Setup

Runs fully locally in about 10 minutes. No paid services required.

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL, installed locally
- API keys: [AviationStack](https://aviationstack.com/), [OpenWeatherMap](https://openweathermap.org/api) (both free tier)

### Database
Create a local database and run the schema + migrations in `database/` (see `database/README.md`).

### Ingestion service
```bash
cd ingestion
pip install -r requirements.txt
cp .env.example .env   # fill in API keys and local DATABASE_URL
python scheduler.py
```

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in local DATABASE_URL
uvicorn main:app --reload
```

### Web dashboard
```bash
cd web-dashboard
npm install
# .env.development already points VITE_API_BASE at localhost:8000
npm run dev
```

### ML scripts
```bash
cd ml
pip install -r requirements.txt
python train_classifier.py
python train_regressor.py
python cascade_link_diagnostic.py
```

## License

MIT