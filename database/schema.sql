-- database/schema.sql
-- Run with: psql -U postgres -d airline_delay_intelligence -f database/schema.sql

CREATE TABLE IF NOT EXISTS airports (
    code            VARCHAR(4) PRIMARY KEY,   -- IATA code, e.g. 'DOH'
    name            VARCHAR(120),
    city            VARCHAR(80),
    country         VARCHAR(80),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    is_hub          BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS flights (
    id                      SERIAL PRIMARY KEY,
    flight_number           VARCHAR(10) NOT NULL,
    airline                 VARCHAR(80),
    origin                  VARCHAR(4) REFERENCES airports(code),
    destination             VARCHAR(4) REFERENCES airports(code),
    scheduled_departure     TIMESTAMP,
    actual_departure        TIMESTAMP,
    scheduled_arrival       TIMESTAMP,
    actual_arrival          TIMESTAMP,
    aircraft_registration   VARCHAR(20),
    status                  VARCHAR(20),        -- scheduled, active, landed, cancelled, incident, diverted
    delay_minutes           INTEGER,
    fetched_at              TIMESTAMP DEFAULT NOW(),
    UNIQUE (flight_number, scheduled_departure)  -- avoid duplicate rows on repeated polling
);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id              SERIAL PRIMARY KEY,
    airport_code    VARCHAR(4) REFERENCES airports(code),
    recorded_at     TIMESTAMP,
    temperature_c   DOUBLE PRECISION,
    wind_speed_ms   DOUBLE PRECISION,
    visibility_m    INTEGER,
    precipitation_mm DOUBLE PRECISION,
    condition_code  VARCHAR(50),
    fetched_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id                          SERIAL PRIMARY KEY,
    flight_id                   INTEGER REFERENCES flights(id),
    predicted_delay_probability DOUBLE PRECISION,
    predicted_delay_minutes     DOUBLE PRECISION,
    model_version                VARCHAR(20),
    predicted_at                 TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cascade_links (
    id                  SERIAL PRIMARY KEY,
    aircraft_registration VARCHAR(20),
    upstream_flight_id    INTEGER REFERENCES flights(id),
    downstream_flight_id  INTEGER REFERENCES flights(id),
    turnaround_minutes    INTEGER,
    created_at            TIMESTAMP DEFAULT NOW()
);

-- Seed the initial hub airport. Add more later (DXB, SIN, etc.)
INSERT INTO airports (code, name, city, country, latitude, longitude, is_hub)
VALUES ('DOH', 'Hamad International Airport', 'Doha', 'Qatar', 25.2731, 51.6081, TRUE)
ON CONFLICT (code) DO NOTHING;
