import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Make sure backend/.env exists and contains "
        "a valid DATABASE_URL pointing at the Railway Postgres instance."
    )

# Single Engine, created once at process startup. This manages a connection
# pool internally -- we are NOT opening one connection for the whole app's
# lifetime, and we are NOT opening a new engine per request. pool_pre_ping
# checks connections are alive before handing them out, which matters for a
# long-running service talking to a remote (Railway) database that may drop
# idle connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Factory that produces a new Session bound to the engine's pool each time
# it's called. autocommit/autoflush left at SQLAlchemy 2.0 defaults.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models (used later in models.py if/when we define
# SQLAlchemy table classes instead of hand-written SQL).
Base = declarative_base()


def get_db():
    """
    FastAPI dependency. Yields one Session per request and guarantees
    it's closed afterward, even if the endpoint raises. Usage in a router:

        @router.get("/flights")
        def list_flights(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()