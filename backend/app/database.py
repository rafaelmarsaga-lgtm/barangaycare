import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "barangaycare.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# In-memory SQLite gives each connection its own empty DB; StaticPool shares one
# connection so tables created at startup are visible to every request (tests).
_in_memory = DATABASE_URL in ("sqlite://", "sqlite:///:memory:")

engine = create_engine(
    DATABASE_URL,
    # FastAPI may run a request on a different thread than the one that opened the connection.
    connect_args={"check_same_thread": False},
    poolclass=StaticPool if _in_memory else None,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: one session per request, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
