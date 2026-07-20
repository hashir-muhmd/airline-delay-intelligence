from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.flights import router as flights_router

app = FastAPI(
    title="SkyPulse API",
    description="Airline delay intelligence API for Doha Hamad International (DOH)",
    version="0.1.0",
)

app.include_router(flights_router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Confirms the API process is up AND the database connection is alive.
    A 200 from the process alone doesn't mean much if Postgres is
    unreachable -- so this runs a trivial query to prove the full path
    works, not just that uvicorn is running.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        return {"status": "degraded", "database": "unreachable", "error": str(exc)}

    return {"status": "ok", "database": db_status}