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
As of 2026-07-11, only 1 of 82 airports in the `airports` table has enriched
metadata (name, city, country, lat/long). The remaining 81 are auto-created
stub rows (code only) from `ensure_airport_exists()`. Enrichment from a public
airport reference dataset (e.g. OurAirports) is a planned next step before
building the map-based dashboard.