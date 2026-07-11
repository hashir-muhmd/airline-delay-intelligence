# Ingestion

Scheduled service that polls flight and weather APIs and writes to PostgreSQL.
Deployed 24/7 on Railway (connected to this repo's `main` branch — pushing
here auto-redeploys).

## Contents
- `aviationstack_client.py` — live flight status/delay data
- `weather_client.py` — OpenWeatherMap airport weather
- `scheduler.py` — polling job (flights ~3x/day to respect AviationStack's
  100 req/month free tier; weather hourly, well within 1,000 req/day free tier)
- `config.py` — tracked airports/routes (includes DOH as primary hub)

Status: running continuously in production on Railway since 2026-07-10.

## Known data characteristics

### Codeshare duplication
AviationStack returns each codeshare flight as a separate record, even when
they refer to the same physical flight (same aircraft, same scheduled/actual
times). Example: a single Doha departure was returned as 9 separate flight
numbers (AS5907, BA2315, MH9052, KQ6205, IB6263, LA6062, B66518, WB1562, AA8218)
— all oneworld or bilateral codeshare partners of the operating carrier.

This is expected airline-industry behavior, not a data bug. Implication:
- Raw `flights` row count overstates true physical flight volume.
- Delay analysis (EDA, ML training) should de-duplicate by grouping on
  (scheduled_departure, actual_departure, origin, destination) before
  computing distributions, so codeshares don't skew delay stats.
- Cascade modeling can safely ignore this, since codeshares share the same
  aircraft rotation anyway.

### Airport enrichment status
Resolved 2026-07-12. All airport rows are enriched with real metadata (name,
city, country, latitude, longitude) sourced from the OurAirports public
dataset (https://ourairports.com/data/airports.csv), matched by IATA code.
See `scripts/enrich_airports.py`. As new airports appear (new routes/
destinations), re-run this script to enrich them — it only updates rows
currently missing name/latitude, so it's safe to re-run anytime.