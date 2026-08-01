# Airline Delay Intelligence (SkyPulse)

AI-powered flight delay prediction and disruption cascade analytics platform, built on real-time flight and weather data, focused on Doha Hamad International (DOH) and Qatar Airways.

**Live dashboard**: https://airline-delay-intelligence.vercel.app
**Live API**: https://amusing-grace-production-54d1.up.railway.app (see `/health` for a quick check — first request after idle may take a few seconds to cold-start)

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
        deployed 24/7 on Railway
                          |
                          v
                  POSTGRESQL
        (flights, weather;
         predictions, cascade links planned)
              deployed on Railway
                          |
                          v
                  ML LAYER
        (delay classifier, delay regressor,
         cascade model, seasonal forecasting)
        NOT STARTED -- blocked on data volume
                          |
                          v
                FASTAPI BACKEND
        deployed live on Railway
        (serverless, scales to zero when idle)
                          |
            +-------------+-------------+
            |                           |
            v                           v
    REACT DASHBOARD              FLUTTER MOBILE APP
    (ops view)                   (traveler-facing alerts)
    live on Vercel                NOT STARTED
    5 pages: Overview, Live Flights,
    Delay Stats, Airports -- fully
    working against live data.
    Cascade Risk = honest
    "in development" placeholder,
    gated on data volume
```

## Tech stack

- **Ingestion**: Python, AviationStack API, OpenWeatherMap API — deployed on Railway
- **Database**: PostgreSQL — deployed on Railway
- **ML**: scikit-learn, XGBoost, Prophet — planned, not yet started
- **Backend**: FastAPI — deployed live on Railway (serverless)
- **Web dashboard**: React + Vite — deployed live on Vercel
- **Mobile app**: Flutter — not started
- **Deployment**: Ingestion, backend, and database run as separate Railway services within one project. Dashboard is a separate Vercel project. Docker Compose not yet set up.

## Status

This project is being built incrementally with real commit history, not uploaded as a finished product. Current progress:

- [x] Ingestion service — deployed 24/7 on Railway, running since 2026-07-10
- [x] Database schema — TIMESTAMPTZ timezone handling, indexes, data-quality constraints
- [x] Airport enrichment — all tracked airports have real name/city/country/coordinates (OurAirports)
- [x] Initial exploratory data analysis — data health checks, codeshare de-duplication, delay distribution
- [x] FastAPI backend — built, tested, deployed live on Railway
- [x] React dashboard — deployed live on Vercel; Overview, Live Flights, Delay Stats, and Airports built and tested against live backend data
- [ ] Cascade Risk dashboard page — shipped as an honest in-app placeholder, gated on data volume (currently ~55 physical flights with delay data)
- [ ] Delay classification + regression models — pending sufficient historical data volume
- [ ] Cascade propagation model — blocked on the same data volume constraint
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
| `ml/` | Training scripts and model artifacts (not yet started) |
| `backend/` | FastAPI service |
| `web-dashboard/` | React ops dashboard |
| `mobile-app/` | Flutter traveler-facing app (not yet started) |

## Known data characteristics

Documented in detail in `ingestion/README.md`:
- **Codeshare duplication** — AviationStack returns each codeshare as a separate flight record, even when multiple flight numbers refer to the same physical flight. Handled via de-duplication logic in the EDA notebook.
- **Timezone handling** — AviationStack mislabels local timestamps with a UTC designator; ingestion re-localizes using the API's separate `timezone` field before converting to true UTC. All timestamp columns use `TIMESTAMPTZ`.

## Known Limitations

**AviationStack free-tier data quality**: The free tier has occasional stale schedules and incomplete fields. Delay values outside plausible bounds (< -60 min or > 720 min) are excluded from analysis, with counts logged transparently rather than silently dropped.

**Codeshare partners**: Some flights list airlines that appear unusual at first glance (e.g. regional or long-haul carriers as partners on Doha routes). These have been cross-checked against Hamad International Airport's own published schedules and confirmed as legitimate codeshare arrangements, not data errors.

**API quota constraints**: The free AviationStack tier is capped at 100 requests/month. Ingestion is scoped to poll once daily for a single tracked airport (DOH) to stay well within budget. A since-fixed scheduler bug (an unconditional poll on every process start, on top of the daily interval) caused occasional over-polling during active development and contributed to a full-quota exhaustion in July 2026; the scheduler now checks data freshness before polling on startup and skips redundant polls.

**Backend cold starts**: The API runs in Railway's serverless mode to control cost. The first request after a period of inactivity may take up to ~10-20 seconds while the service spins up.

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use a hosted instance, e.g. Railway)
- API keys: [AviationStack](https://aviationstack.com/), [OpenWeatherMap](https://openweathermap.org/api)

### Ingestion service
```bash
cd ingestion
pip install -r requirements.txt
cp .env.example .env   # fill in API keys and DATABASE_URL
python scheduler.py
```

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL
uvicorn main:app --reload
```

### Web dashboard
```bash
cd web-dashboard
npm install
# .env.development already points VITE_API_BASE at localhost:8000
npm run dev
```

For a working reference without any local setup, see the live dashboard and API links at the top of this README.

## License

MIT