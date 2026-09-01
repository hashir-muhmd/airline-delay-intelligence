"""
Minimal backend test suite. Hits real endpoints against whatever database
DATABASE_URL currently points at (local Postgres in normal dev use) --
these are integration tests, not isolated unit tests with a mocked DB,
since the endpoints themselves are thin wrappers around real SQL queries
and the value is in confirming the whole path (route -> query -> response
schema) actually works end-to-end.

Run with:
    cd backend
    pytest
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_list_flights_returns_200():
    response = client.get("/flights?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    # limit=5 should never return more than 5, regardless of DB contents
    assert len(body) <= 5


def test_list_airports_returns_200():
    response = client.get("/airports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delay_stats_returns_valid_shape():
    response = client.get("/stats/delays")
    assert response.status_code == 200
    body = response.json()
    # These keys must always be present, whether or not there's enough
    # data yet for a full distribution (see MIN_FLIGHTS_FOR_STATS in
    # routers/flights.py).
    assert "physical_flights_total" in body
    assert "count" in body


def test_cascade_stats_returns_valid_shape():
    response = client.get("/cascade/stats")
    assert response.status_code == 200
    body = response.json()
    assert "candidate_count" in body
    assert "flights_with_icao24" in body
    assert body["candidate_count"] >= 0


def test_get_nonexistent_flight_returns_404():
    response = client.get("/flights/999999999")
    assert response.status_code == 404