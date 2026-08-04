# Ingestion

Scheduled service that polls flight and weather APIs and writes to PostgreSQL.
Deployed 24/7 on Railway. Auto-redeploys only when files under `ingestion/`
change (Watch Paths scoped to `/ingestion/**`).

## Contents
- `aviationstack_client.py` — live flight status/delay data, including
  timezone resolution (see below)
- `weather_client.py` — OpenWeatherMap airport weather
- `scheduler.py` — polling job (flights once daily to respect AviationStack's
  100 req/month free tier; weather hourly, well within 1,000 req/day free tier)
- `config.py` — tracked airports/routes (currently DOH only, as primary hub)

Status: running continuously in production on Railway since 2026-07-10.

## Startup-poll quota safeguard

Earlier versions of the scheduler ran an immediate flight poll on every
process start, in addition to the normal 24-hour interval job. Since
`TRACKED_AIRPORTS` is DOH-only, expected usage is a safe 60 calls/month, but
frequent restarts/redeploys during active development caused this startup
poll to fire repeatedly, consuming extra quota beyond the intended 1 call/day
and contributing to a full quota exhaustion in July 2026.

**Fixed**: the scheduler now checks the most recent `fetched_at` timestamp in
the `flights` table on startup. If existing data is less than 20 hours old,
the startup poll is skipped and only the normal 24-hour interval job runs. If
that freshness check itself fails for any reason, the scheduler defaults to
**not** skipping — favoring occasional over-polling over silently never
polling at all.

## Known data characteristics

### Timezone handling
AviationStack returns local timestamps but labels them with a UTC offset
(effectively mislabeling local time as UTC). Ingestion re-localizes each
timestamp using the API's separate `timezone` field before converting to true
UTC. All DB timestamp columns are `TIMESTAMPTZ`. A historical backfill (~5,100
rows) was run after this fix shipped to correct previously ingested data.

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

### `aircraft_registration` is always null on the free tier — use `aircraft_icao24` instead
Confirmed via direct inspection of raw AviationStack API responses (multiple
active DOH flights checked): `aircraft.registration` (the human-readable tail
number, e.g. "A7-BCD") comes back `null` on every single flight, regardless
of flight status. This is not a parsing bug in `_flight_to_row()` — the field
is genuinely absent in AviationStack's response on the free tier.

However, `aircraft.icao24` (the aircraft's Mode-S transponder hex code, e.g.
`"06A2F7"`) **is** populated and confirmed working. It's a less
human-readable identifier than a tail number, but it's a real, stable,
per-aircraft unique ID — sufficient for linking flights to the same physical
aircraft for cascade-delay modeling, which is all `aircraft_registration` was
ever needed for in this project.

As a result: `flights.aircraft_icao24` and `cascade_links.aircraft_icao24`
were added (migrations `004` and `005`), and ingestion now captures
`icao24` alongside the still-present-but-always-null `registration` field
(kept in the schema rather than dropped, in case a future paid-tier upgrade
ever populates it — no schema change would be needed to start using it then).

**Note**: this only affects flights ingested after this fix shipped.
Historical rows ingested before this change have `aircraft_icao24 = NULL`
retroactively, since the raw API responses at the time weren't stored beyond
what was mapped into the schema then in use — there's nothing to backfill
from.

### Airport enrichment status
Resolved 2026-07-12. All airport rows are enriched with real metadata (name,
city, country, latitude, longitude) sourced from the OurAirports public
dataset (https://ourairports.com/data/airports.csv), matched by IATA code.
See `scripts/enrich_airports.py`. As new airports appear (new routes/
destinations), re-run this script to enrich them — it only updates rows
currently missing name/latitude, so it's safe to re-run anytime.

### AviationStack free-tier data quality under quota pressure
When the monthly quota is exhausted, AviationStack has occasionally returned
degraded or placeholder-like data (mismatched timestamps, a non-existent
airline name) rather than cleanly erroring out on every request. If unusual
rows appear (e.g. an unrecognized airline code), check whether they coincide
with a quota-exhaustion window before assuming a code-level bug.

# git add ingestion/README.md
git commit -m "Document aircraft_registration free-tier limitation and aircraft_icao24 resolution in ingestion README"
git push