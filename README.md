# Airline Delay Intelligence

AI-powered flight delay prediction and disruption cascade analytics platform, built on real-time flight and weather data.

## Problem

Flight delays are one of the largest cost and customer-experience drivers in airline operations. A single delayed inbound aircraft can cascade into delays across its next several scheduled legs if turnaround buffers aren't enough to absorb the loss of time. This project predicts individual flight delays and estimates how those delays propagate downstream through an aircraft's rotation — the kind of analysis airline ops control centers rely on, focused around Doha Hamad International (DOH) as the primary hub.

## Architecture

```
External APIs (AviationStack, OpenWeatherMap, AeroDataBox)
        |
Scheduled ingestion service (polls daily, quota-aware)
        |
PostgreSQL (flights, weather, predictions, cascade links)
        |
   ML layer (delay classifier, delay regressor, cascade model, seasonal forecasting)
        |
   FastAPI backend  -- deployed live on Railway (serverless, scales to zero when idle)
        |
  ------+------
  |            |
React dashboard   Flutter mobile app
(ops view)        (traveler-facing alerts)
  4 of 5 pages built and tested against live data
```

## Tech stack

- **Ingestion**: Python, AviationStack API, OpenWeatherMap API
- **Database**: PostgreSQL (Railway, cloud-hosted)
- **ML**: scikit-learn, XGBoost, Prophet
- **Backend**: FastAPI, deployed on Railway
- **Web dashboard**: React + Vite
- **Mobile app**: Flutter
- **Deployment**: Ingestion, backend, and database each deployed as separate Railway services within one project; Docker Compose not yet set up

## Status

This project is being built incrementally with real commit history, not uploaded as a finished product. Current progress:

- [x] Ingestion service — deployed 24/7 on Railway, running since 2026-07-10
- [x] Database schema — includes TIMESTAMPTZ timezone handling, indexes, and data-quality constraints
- [x] Airport enrichment — all tracked airports have real name/city/country/coordinates (sourced from OurAirports)
- [x] Initial exploratory data analysis — data health checks, codeshare de-duplication logic, delay distribution
- [x] FastAPI backend — built, tested, and deployed on Railway
- [x] React dashboard — Overview, Live Flights, Delay Stats, and Airports pages built and tested against live backend data
- [ ] Delay classification + regression models — pending sufficient historical data volume
- [ ] Cascade propagation model / Cascade Risk dashboard page — blocked on the same data volume constraint
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
- **Timezone handling** — all timestamp columns use `TIMESTAMPTZ` to avoid ambiguity across the many timezones this project spans.

## Known Limitations

**AviationStack free-tier data quality**: The free tier has occasional stale schedules and incomplete fields. Delay values outside plausible bounds (< -60 min or > 720 min) are excluded from analysis, with counts logged transparently rather than silently dropped.

**Codeshare partners**: Some flights list airlines that appear unusual at first glance (e.g. regional or long-haul carriers as partners on Doha routes). These have been cross-checked against Hamad International Airport's own published schedules and confirmed as legitimate codeshare arrangements, not data errors.

**API quota constraints**: The free AviationStack tier is capped at 100 requests/month, so ingestion polls once daily rather than in real-time.

## Setup

Setup instructions will be added as each component is built.

## License

MIT