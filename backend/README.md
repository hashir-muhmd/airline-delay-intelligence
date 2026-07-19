# Backend

FastAPI service serving predictions and historical data to the web dashboard and mobile app.

Planned contents:
- `main.py` — app entrypoint
- `routers/flights.py`, `routers/predictions.py`, `routers/cascade.py`
- `schemas.py` — Pydantic models

Status: not yet implemented — scaffolding and dependencies added, endpoints coming next.

Planned first endpoints:
- `GET /flights` — list flights with optional filters
- `GET /flights/{id}` — single flight detail
- `GET /airports` — list tracked airports
- `GET /stats/delays` — aggregate delay statistics

Run locally with: `uvicorn main:app --reload` (once `main.py` exists)