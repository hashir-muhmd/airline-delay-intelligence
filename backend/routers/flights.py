from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import AirportOut, DelayStatsOut, FlightOut, PhysicalFlightOut

router = APIRouter()

# Matches the threshold used in notebooks/01_eda.ipynb ("if len(delayed) > 5")
# before it's considered worth showing a distribution rather than a
# "not enough data yet" message.
MIN_FLIGHTS_FOR_STATS = 5

# Plausible bounds for delay_minutes. Commercial flights essentially never
# depart more than ~60 min ahead of schedule, and delays stretching past
# ~12 hours are more likely bad data (e.g. AviationStack returning a stale
# or mismatched actual_departure from a different day) than a genuine
# still-active delay. Found via a real case: QR8407 on 2026-07-14 showed
# delay_minutes = -847 because actual_departure was ~14 hours before its
# own scheduled_departure -- physically impossible for that flight.
MIN_PLAUSIBLE_DELAY_MINUTES = -60
MAX_PLAUSIBLE_DELAY_MINUTES = 720


@router.get("/airports", response_model=list[AirportOut])
def list_airports(db: Session = Depends(get_db)):
    """
    List all airports. Useful later for the dashboard's map view since
    every airport row now has real name/city/country/lat/long from the
    OurAirports enrichment pass.
    """
    result = db.execute(
        text(
            """
            SELECT code, name, city, country, latitude, longitude, is_hub
            FROM airports
            ORDER BY code
            """
        )
    )
    rows = result.mappings().all()
    return [AirportOut.model_validate(dict(row)) for row in rows]


@router.get("/flights", response_model=list[FlightOut])
def list_flights(
    limit: int = Query(50, ge=1, le=500, description="Max rows to return"),
    origin: Optional[str] = Query(None, min_length=3, max_length=3, description="Filter by origin IATA code"),
    status: Optional[str] = Query(None, description="Filter by flight status"),
    db: Session = Depends(get_db),
):
    """
    List flights with optional filters. Ordered by most recently
    scheduled first. No de-duplication of codeshares here -- that's an
    EDA/analytics concern (see notebooks/01_eda.ipynb); this endpoint
    returns raw flights rows as-is.
    """
    query = """
        SELECT id, flight_number, airline, origin, destination,
               scheduled_departure, actual_departure,
               scheduled_arrival, actual_arrival,
               aircraft_registration, status, delay_minutes, fetched_at
        FROM flights
        WHERE 1=1
    """
    params = {}

    if origin:
        query += " AND origin = :origin"
        params["origin"] = origin.upper()

    if status:
        query += " AND status = :status"
        params["status"] = status

    query += " ORDER BY scheduled_departure DESC NULLS LAST LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.mappings().all()
    return [FlightOut.model_validate(dict(row)) for row in rows]


@router.get("/flights/physical", response_model=list[PhysicalFlightOut])
def list_physical_flights(
    limit: int = Query(50, ge=1, le=500, description="Max rows to return"),
    origin: Optional[str] = Query(None, min_length=3, max_length=3, description="Filter by origin IATA code"),
    destination: Optional[str] = Query(None, min_length=3, max_length=3, description="Filter by destination IATA code"),
    db: Session = Depends(get_db),
):
    """
    De-duplicated physical flights, with codeshares collapsed into a
    single row each. Mirrors notebooks/01_eda.ipynb's aggregation:
    grouped on (scheduled_departure, actual_departure, origin,
    destination), flight_numbers joined as a comma-separated string,
    and single-valued fields (airline, status, delay_minutes, etc.)
    taken as the "first" row after sorting by flight_number -- same
    tie-break rule the notebook uses.

    Unlike GET /flights, this collapses codeshares (e.g. 9 marketing
    flight numbers for one physical departure) into one row, so
    num_codeshares > 1 tells you a flight is shared across airlines.

    NOTE: this must be registered BEFORE /flights/{flight_id} below --
    FastAPI/Starlette matches routes in registration order, and a literal
    path segment like "physical" would otherwise be swallowed by the
    {flight_id}: int path parameter, causing a 422 int-parsing error.
    """
    query = """
        SELECT
            scheduled_departure, actual_departure, origin, destination,
            string_agg(flight_number, ', ' ORDER BY flight_number) AS flight_numbers,
            COUNT(flight_number) AS num_codeshares,
            (array_agg(airline ORDER BY flight_number))[1] AS airline_primary,
            (array_agg(scheduled_arrival ORDER BY flight_number))[1] AS scheduled_arrival,
            (array_agg(actual_arrival ORDER BY flight_number))[1] AS actual_arrival,
            (array_agg(status ORDER BY flight_number))[1] AS status,
            (array_agg(delay_minutes ORDER BY flight_number))[1] AS delay_minutes,
            (array_agg(aircraft_registration ORDER BY flight_number))[1] AS aircraft_registration
        FROM flights
        WHERE 1=1
    """
    params = {}

    if origin:
        query += " AND origin = :origin"
        params["origin"] = origin.upper()

    if destination:
        query += " AND destination = :destination"
        params["destination"] = destination.upper()

    query += """
        GROUP BY scheduled_departure, actual_departure, origin, destination
        ORDER BY scheduled_departure DESC NULLS LAST
        LIMIT :limit
    """
    params["limit"] = limit

    result = db.execute(text(query), params)
    rows = result.mappings().all()
    return [PhysicalFlightOut.model_validate(dict(row)) for row in rows]


@router.get("/flights/{flight_id}", response_model=FlightOut)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    """Single flight detail by primary key id."""
    result = db.execute(
        text(
            """
            SELECT id, flight_number, airline, origin, destination,
                   scheduled_departure, actual_departure,
                   scheduled_arrival, actual_arrival,
                   aircraft_registration, status, delay_minutes, fetched_at
            FROM flights
            WHERE id = :flight_id
            """
        ),
        {"flight_id": flight_id},
    )
    row = result.mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Flight with id {flight_id} not found")

    return FlightOut.model_validate(dict(row))


@router.get("/stats/delays", response_model=DelayStatsOut)
def get_delay_stats(db: Session = Depends(get_db)):
    """
    Delay distribution over de-duplicated physical flights, computed live
    from current DB state. Mirrors the logic in notebooks/01_eda.ipynb:

    1. De-duplicate codeshares into physical flights via DISTINCT ON,
       grouping on (scheduled_departure, actual_departure, origin,
       destination) and breaking ties by flight_number -- same grouping
       key and tie-break rule the notebook uses.
    2. Compute distribution stats only over physical flights with a
       non-null delay_minutes.
    3. If there isn't enough delay data yet, return a message instead of
       misleading statistics (matching the notebook's own
       "if len(delayed) > 5" plotting guard).
    """
    result = db.execute(
        text(
            """
            WITH physical_flights AS (
                SELECT DISTINCT ON (scheduled_departure, actual_departure, origin, destination)
                    scheduled_departure, actual_departure, origin, destination,
                    delay_minutes
                FROM flights
                ORDER BY scheduled_departure, actual_departure, origin, destination, flight_number
            ),
            plausible AS (
                SELECT delay_minutes
                FROM physical_flights
                WHERE delay_minutes IS NOT NULL
                  AND delay_minutes BETWEEN :min_delay AND :max_delay
            )
            SELECT
                (SELECT COUNT(*) FROM physical_flights) AS physical_flights_total,
                (SELECT COUNT(*) FROM physical_flights WHERE delay_minutes IS NOT NULL) AS physical_flights_with_delay_data,
                (SELECT COUNT(*) FROM physical_flights
                    WHERE delay_minutes IS NOT NULL
                    AND delay_minutes NOT BETWEEN :min_delay AND :max_delay) AS physical_flights_excluded_anomalous,
                (SELECT COUNT(*) FROM plausible) AS count,
                (SELECT AVG(delay_minutes) FROM plausible) AS mean_minutes,
                (SELECT MIN(delay_minutes) FROM plausible) AS min_minutes,
                (SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY delay_minutes) FROM plausible) AS p25_minutes,
                (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_minutes) FROM plausible) AS median_minutes,
                (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY delay_minutes) FROM plausible) AS p75_minutes,
                (SELECT MAX(delay_minutes) FROM plausible) AS max_minutes
            """
        ),
        {
            "min_delay": MIN_PLAUSIBLE_DELAY_MINUTES,
            "max_delay": MAX_PLAUSIBLE_DELAY_MINUTES,
        },
    )
    row = result.mappings().first()

    physical_flights_total = row["physical_flights_total"]
    excluded_anomalous = row["physical_flights_excluded_anomalous"]
    count = row["count"]

    if count <= MIN_FLIGHTS_FOR_STATS:
        return DelayStatsOut(
            physical_flights_total=physical_flights_total,
            physical_flights_with_delay_data=row["physical_flights_with_delay_data"],
            physical_flights_excluded_anomalous=excluded_anomalous,
            count=count,
            message=(
                f"Not enough plausible delay data yet for a meaningful distribution "
                f"({count} physical flights within plausible bounds; need more than "
                f"{MIN_FLIGHTS_FOR_STATS}). Revisit after more ingestion."
            ),
        )

    return DelayStatsOut(
        physical_flights_total=physical_flights_total,
        physical_flights_with_delay_data=row["physical_flights_with_delay_data"],
        physical_flights_excluded_anomalous=excluded_anomalous,
        count=count,
        mean_minutes=round(row["mean_minutes"], 2) if row["mean_minutes"] is not None else None,
        min_minutes=row["min_minutes"],
        p25_minutes=row["p25_minutes"],
        median_minutes=row["median_minutes"],
        p75_minutes=row["p75_minutes"],
        max_minutes=row["max_minutes"],
        message=(
            f"{excluded_anomalous} physical flight(s) excluded as anomalous "
            f"(delay outside {MIN_PLAUSIBLE_DELAY_MINUTES} to {MAX_PLAUSIBLE_DELAY_MINUTES} minutes)."
            if excluded_anomalous > 0 else None
        ),
    )