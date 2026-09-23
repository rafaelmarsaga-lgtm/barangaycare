from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registers the tables on Base before create_all)
from app.database import Base, engine
from app.routers import appointments, slots, summary
from app.schemas import FALLBACK_MESSAGE, FRIENDLY_MESSAGES

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="BarangayCare", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def friendly_validation_error(request: Request, exc: RequestValidationError):
    """Every error body has one shape, {"detail": "<message>"}, so the UI can show
    detail as-is. Reports the first failing field; unknown fields get a generic message."""
    first_error = exc.errors()[0]
    field = first_error["loc"][-1] if first_error.get("loc") else None
    message = FRIENDLY_MESSAGES.get(field, FALLBACK_MESSAGE)
    return JSONResponse(status_code=422, content={"detail": message})


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(appointments.router)
app.include_router(slots.router)
app.include_router(summary.router)

# Mounted last so the /api routes above take priority over static files.
# Same origin for page and API means no CORS setup is needed.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
