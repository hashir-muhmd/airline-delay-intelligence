# ingestion/db.py
"""
Simple psycopg2 connection helper for the ingestion service.
"""

import psycopg2
from config import DATABASE_URL


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def insert_flight(conn, flight: dict):
    """
    Insert a flight row, skipping duplicates (same flight_number + scheduled_departure).
    Returns the flight id (existing or newly inserted).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO flights (
                flight_number, airline, origin, destination,
                scheduled_departure, actual_departure,
                scheduled_arrival, actual_arrival,
                aircraft_registration, status, delay_minutes
            )
            VALUES (%(flight_number)s, %(airline)s, %(origin)s, %(destination)s,
                    %(scheduled_departure)s, %(actual_departure)s,
                    %(scheduled_arrival)s, %(actual_arrival)s,
                    %(aircraft_registration)s, %(status)s, %(delay_minutes)s)
            ON CONFLICT (flight_number, scheduled_departure)
            DO UPDATE SET
                actual_departure = EXCLUDED.actual_departure,
                actual_arrival = EXCLUDED.actual_arrival,
                status = EXCLUDED.status,
                delay_minutes = EXCLUDED.delay_minutes,
                fetched_at = NOW()
            RETURNING id;
            """,
            flight,
        )
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None


def insert_weather_snapshot(conn, snapshot: dict):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO weather_snapshots (
                airport_code, recorded_at, temperature_c, wind_speed_ms,
                visibility_m, precipitation_mm, condition_code
            )
            VALUES (%(airport_code)s, %(recorded_at)s, %(temperature_c)s, %(wind_speed_ms)s,
                    %(visibility_m)s, %(precipitation_mm)s, %(condition_code)s);
            """,
            snapshot,
        )
        conn.commit()
