from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import AirportOut, DelayStatsOut, FlightOut

router = APIRouter()

# Matches the threshold used in notebooks/01_eda.ipynb ("if len(delayed) > 5")
# before it's considered worth showing a distribution rather than a
# "not enough data yet" message.
MIN_FLIGHTS_FOR_STATS = 5


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
            )
            SELECT
                COUNT(*) AS physical_flights_total,
                COUNT(delay_minutes) AS physical_flights_with_delay_data,
                AVG(delay_minutes) AS mean_minutes,
                MIN(delay_minutes) AS min_minutes,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY delay_minutes) AS p25_minutes,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delay_minutes) AS median_minutes,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY delay_minutes) AS p75_minutes,
                MAX(delay_minutes) AS max_minutes
            FROM physical_flights
            """
        )
    )
    row = result.mappings().first()

    physical_flights_total = row["physical_flights_total"]
    count = row["physical_flights_with_delay_data"]

    if count <= MIN_FLIGHTS_FOR_STATS:
        return DelayStatsOut(
            physical_flights_total=physical_flights_total,
            physical_flights_with_delay_data=count,
            count=count,
            message=(
                f"Not enough delay data yet for a meaningful distribution "
                f"({count} physical flights with delay data; need more than "
                f"{MIN_FLIGHTS_FOR_STATS}). Revisit after more ingestion."
            ),
        )

    return DelayStatsOut(
        physical_flights_total=physical_flights_total,
        physical_flights_with_delay_data=count,
        count=count,
        mean_minutes=round(row["mean_minutes"], 2) if row["mean_minutes"] is not None else None,
        min_minutes=row["min_minutes"],
        p25_minutes=row["p25_minutes"],
        median_minutes=row["median_minutes"],
        p75_minutes=row["p75_minutes"],
        max_minutes=row["max_minutes"],
    )