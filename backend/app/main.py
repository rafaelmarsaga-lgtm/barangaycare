from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registers the tables on Base before create_all)
from app.database import Base, engine

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="BarangayCare", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Mounted last so the /api routes above take priority over static files.
# Same origin for page and API means no CORS setup is needed.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
