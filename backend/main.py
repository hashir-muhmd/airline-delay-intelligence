from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.flights import router as flights_router

app = FastAPI(
    title="SkyPulse API",
    description="Airline delay intelligence API for Doha Hamad International (DOH)",
    version="0.1.0",
)

# CORS: without this, a browser-based React dashboard running on a
# different origin (e.g. localhost:3000 or 5173 locally, or a deployed
# domain later) would have every fetch() call to this API silently
# blocked by the browser itself -- not a FastAPI restriction, a standard
# browser security rule for cross-origin requests. This is a read-only
# API (GET endpoints only, no auth/cookies yet), so a permissive origin
# list here is low-risk for now.
#
# Includes both common local dev ports since Create React App defaults
# to 3000 and Vite defaults to 5173 -- add the real deployed dashboard
# URL here once it exists.
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
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