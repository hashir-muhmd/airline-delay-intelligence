from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import AirportOut, FlightOut

router = APIRouter()


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