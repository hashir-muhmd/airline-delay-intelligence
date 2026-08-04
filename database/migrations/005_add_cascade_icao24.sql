-- 005_add_cascade_icao24.sql
--
-- cascade_links was originally designed to link upstream/downstream flights
-- by aircraft_registration. Per the investigation in
-- ingestion/README.md / 004_add_aircraft_icao24.sql, aircraft_registration
-- is confirmed always null on AviationStack's free tier -- so this table
-- needs the same aircraft_icao24 fallback identifier that was added to
-- flights, or cascade modeling would never have a usable linking field.
--
-- This table has no data in it yet (ML/cascade work hasn't started), so
-- this is a pure additive change -- no backfill needed.

ALTER TABLE cascade_links
    ADD COLUMN IF NOT EXISTS aircraft_icao24 VARCHAR(10);