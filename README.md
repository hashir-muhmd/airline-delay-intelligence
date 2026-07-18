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
   FastAPI backend
        |
  ------+------
  |            |
React dashboard   Flutter mobile app
(ops view)        (traveler-facing alerts)
```

## Tech stack

- **Ingestion**: Python, AviationStack API, OpenWeatherMap API
- **Database**: PostgreSQL (Railway, cloud-hosted)
- **ML**: scikit-learn, XGBoost, Prophet
- **Backend**: FastAPI
- **Web dashboard**: React
- **Mobile app**: Flutter
- **Deployment**: Docker Compose (ingestion currently deployed standalone on Railway)

## Status

This project is being built incrementally with real commit history, not uploaded as a finished product. Current progress:

- [x] Ingestion service — deployed 24/7 on Railway, running since 2026-07-10
- [x] Database schema — includes TIMESTAMPTZ timezone handling, indexes, and data-quality constraints
- [x] Airport enrichment — all tracked airports have real name/city/country/coordinates (sourced from OurAirports)
- [x] Initial exploratory data analysis — data health checks, codeshare de-duplication logic, delay distribution
- [ ] Delay classification + regression models — pending sufficient historical data volume
- [ ] Cascade propagation model
- [ ] Seasonal delay forecasting
- [ ] FastAPI backend
- [ ] React dashboard
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

## Setup

Setup instructions will be added as each component is built.

## License

MIT