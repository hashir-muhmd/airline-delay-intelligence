-- 004_add_aircraft_icao24.sql
--
-- aircraft_registration has been confirmed (via direct raw API testing) to
-- always be null on AviationStack's free tier -- this is a data ceiling,
-- not a parsing bug (see ingestion/README.md for the investigation).
--
-- icao24 (the aircraft's Mode-S transponder hex code) IS populated on the
-- free tier and is a usable, stable per-aircraft identifier -- not as
-- human-readable as a tail number, but sufficient for linking flights to
-- the same physical aircraft for cascade-delay modeling.
--
-- aircraft_registration is left in place rather than dropped: harmless to
-- keep, and if a future paid-tier upgrade ever populates it, no schema
-- change would be needed to start using it.

ALTER TABLE flights
    ADD COLUMN IF NOT EXISTS aircraft_icao24 VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_flights_aircraft_icao24
    ON flights (aircraft_icao24);