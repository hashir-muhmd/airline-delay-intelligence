# Ingestion

Scheduled service that polls flight and weather APIs and writes to PostgreSQL. Runs locally via `python scheduler.py`. Previously deployed 24/7 on Railway from 2026-07-10 through August 2026 — see the root `README.md`'s "Deployment history" section for what happened and why it's local-only now.

## Contents
- `aviationstack_client.py` — live flight status/delay data, including
  timezone resolution (see below)
- `weather_client.py` — OpenWeatherMap airport weather
- `scheduler.py` — polling job (flights once daily to respect AviationStack's
  100 req/month free tier; weather hourly, well within 1,000 req/day free tier)
- `config.py` — tracked airports/routes (currently DOH only, as primary hub)

Status: runs on-demand or continuously (while the process stays open) on
whichever machine it's started on. No longer running 24/7 in the cloud.

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
polling at all. This safeguard remains just as relevant running locally,
since restarting the local process (e.g. after closing a terminal) is now
the equivalent of the redeploys that originally triggered the problem.

## Known data characteristics

### Timezone handling
AviationStack returns local timestamps but labels them with a UTC offset
(effectively mislabeling local time as UTC). Ingestion re-localizes each
timestamp using the API's separate `timezone` field before converting to true
UTC. All DB timestamp columns are `TIMESTAMPTZ`. A historical backfill (~5,100
rows) was run on the (now-retired) Railway-hosted database after this fix
shipped, to correct previously ingested data.

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

### "AlphaSky" codeshare entries — real airline, implausible codeshare (unresolved)
Occasionally an `AS`-prefixed flight number (e.g. `AS5903`) appears as a
codeshare partner on a Qatar Airways route, attributed to the airline name
"AlphaSky". **AlphaSky is confirmed to be a real airline** (Alpha Sky LLP, a
small cargo carrier based in Shymkent, Kazakhstan, IATA code `AS`, ICAO code
`JAG`, founded 2023) — this is not fabricated/garbage data the way a
non-existent airline name would be.

However, it's implausible as an actual codeshare partner: cargo carriers
essentially never codeshare passenger flights, and a 4-aircraft Kazakhstan
cargo operator codesharing a Dhaka–Doha passenger route with Qatar Airways
doesn't match normal airline commercial practice. The more likely
explanation is an **IATA code collision** — `AS` is a short, commonly
reused 2-letter code, and AviationStack's airline-code resolution may be
misattributing a different actual `AS`-coded carrier to "AlphaSky."

**Not yet root-caused.** Documented here so this doesn't get mistaken for
either (a) fabricated/garbage data, since AlphaSky is real, or (b) a
legitimate codeshare, since the pairing doesn't make operational sense.
Treat `AS`-attributed codeshare entries with caution in any analysis that
depends on airline identity being correct; the flight's route/timing data
itself is likely still accurate, only the codeshare airline attribution is
in question.

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

**Correction (2026-08-05)**: an earlier version of this note claimed
`icao24` only populates once a flight transitions to `"active"` status,
by analogy with how `registration` seemed tied to live tracking data. Direct
observation of the live dashboard has since shown this to be **inaccurate**:
several still-`"scheduled"` flights already carry a real `icao24` value
(e.g. `AI9110` DOH→COK, `MH9321` DOH→IST), meaning the airframe assigned to
a scheduled rotation is often already known to AviationStack ahead of
departure, not only once transponder tracking begins. Coverage is still
partial, though — many scheduled flights in the same dashboard view showed
`null` — so availability appears to depend more on the airline/route than
on flight status specifically. Treat `icao24` as "populated for a
meaningful subset of flights, not guaranteed for any given one," rather
than "only available once active."

**Note**: this only affects flights ingested after this fix shipped.
Historical rows ingested before this change have `aircraft_icao24 = NULL`
retroactively, since the raw API responses at the time weren't stored beyond
what was mapped into the schema then in use — there's nothing to backfill
from.

### Airport enrichment status
Resolved 2026-07-12, and re-verified 2026-08-05 after a re-run of
`scripts/enrich_airports.py` picked up 40 newly-appeared stub rows (new
destinations added since the original enrichment pass) — all 40 matched
successfully against OurAirports, bringing coverage to 167/167 (100%) on the
Railway-hosted dataset at the time. Following the move to local development,
the same script was re-run against the smaller local dataset (2026-08-23)
and again reached 100% coverage (97/97 airports referenced at that point,
0 unmatched). As new destinations continue to appear through local
ingestion, re-run this script periodically; it's safe to re-run anytime
since it only updates rows currently missing name/latitude.

### AviationStack free-tier data quality under quota pressure
When the monthly quota is exhausted, AviationStack has occasionally returned
degraded or placeholder-like data (mismatched timestamps, a non-existent
airline name) rather than cleanly erroring out on every request. If unusual
rows appear (e.g. an unrecognized airline code), check whether they coincide
with a quota-exhaustion window before assuming a code-level bug. Note that
the "AlphaSky" anomaly above was observed under healthy, non-exhausted quota
conditions (6/100 used), so it's a separate issue from this one, not another
instance of it.