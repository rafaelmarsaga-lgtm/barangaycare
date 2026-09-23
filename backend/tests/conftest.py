import os

# Must be set before the app is imported: database.py reads it at import time,
# so tests never touch the real barangaycare.db file.
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services.booking import PH_TZ, now_ph

# Same fixed clock as the unit tests: Thursday 24 Sep 2026, 2:10 PM PH time.
FIXED_NOW = datetime(2026, 9, 24, 14, 10, tzinfo=PH_TZ)


@pytest.fixture
def client():
    # Endpoints get "now" through Depends(now_ph); pin it so date rules are testable.
    app.dependency_overrides[now_ph] = lambda: FIXED_NOW
    # "with" runs the lifespan handler, which creates the tables.
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    # Fresh, empty database for every test.
    Base.metadata.drop_all(bind=engine)
