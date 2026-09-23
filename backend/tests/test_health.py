def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_appointments_table_exists(client):
    # Lifespan must have created the table, or every later endpoint fails with "no such table".
    from sqlalchemy import inspect

    from app.database import engine

    assert "appointments" in inspect(engine).get_table_names()


def test_frontend_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "BarangayCare" in response.text
