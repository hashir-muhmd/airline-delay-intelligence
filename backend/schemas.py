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