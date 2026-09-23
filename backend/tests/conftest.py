import os

# Must be set before the app is imported: database.py reads it at import time,
# so tests never touch the real barangaycare.db file.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
def client():
    # "with" runs the lifespan handler, which creates the tables.
    with TestClient(app) as test_client:
        yield test_client
    # Fresh, empty database for every test.
    Base.metadata.drop_all(bind=engine)
