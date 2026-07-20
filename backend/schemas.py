from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AirportOut(BaseModel):
    """Response shape for a row from the airports table."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_hub: Optional[bool] = None


class FlightOut(BaseModel):
    """Response shape for a row from the flights table."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    flight_number: str
    airline: Optional[str] = None
    origin: str
    destination: str
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    aircraft_registration: Optional[str] = None
    status: str
    delay_minutes: Optional[int] = None
    fetched_at: Optional[datetime] = None


class DelayStatsOut(BaseModel):
    """
    Response shape for GET /stats/delays. Mirrors the de-duplicated
    delay distribution computed in notebooks/01_eda.ipynb, but as a live
    query against current data rather than a notebook snapshot.
    """

    physical_flights_total: int
    physical_flights_with_delay_data: int
    physical_flights_excluded_anomalous: int
    count: int
    mean_minutes: Optional[float] = None
    min_minutes: Optional[int] = None
    p25_minutes: Optional[float] = None
    median_minutes: Optional[float] = None
    p75_minutes: Optional[float] = None
    max_minutes: Optional[int] = None
    message: Optional[str] = None


class PhysicalFlightOut(BaseModel):
    """
    Response shape for GET /flights/physical -- a de-duplicated physical
    flight, with codeshares collapsed into flight_numbers/num_codeshares.
    Mirrors the aggregation in notebooks/01_eda.ipynb exactly (same
    grouping key, same "first after sorting by flight_number" tie-break
    for single-valued fields).
    """

    model_config = ConfigDict(from_attributes=True)

    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    origin: str
    destination: str
    flight_numbers: str
    num_codeshares: int
    airline_primary: Optional[str] = None
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str
    delay_minutes: Optional[int] = None
    aircraft_registration: Optional[str] = None