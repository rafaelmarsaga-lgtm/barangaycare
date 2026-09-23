# BarangayCare — Barangay Health Center Appointment System

Residents book check-ups online; the system blocks double booking, past dates, Sundays and
invalid contact numbers. Staff view each day's appointments, mark them Completed or
No-show, and see a daily summary.

IT 415 lab exam project · FastAPI + SQLite backend, HTML + vanilla JS + Tailwind (CDN) frontend.

## Run it

Requires Python 3.11+.

```bash
cd backend
pip install -r requirements.txt
python seed_data.py                 # optional: reset DB with 9 sample appointments
python -m uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/** (API docs: http://127.0.0.1:8000/docs).

## Test it

```bash
cd backend
python -m pytest -v                 # 73 tests
```

## Project layout

```
backend/
  app/
    main.py            app, lifespan (creates tables), friendly 422 handler, static files
    database.py        engine, session, Base (DATABASE_URL env var; tests use in-memory)
    models.py          Appointment table, UNIQUE(appointment_date, time_slot)
    schemas.py         Pydantic request/response models + friendly messages
    routers/           appointments.py, slots.py, summary.py
    services/          booking.py (rules), summary.py (daily summary) — pure, unit-tested
  tests/               73 pytest tests
  seed_data.py
frontend/
  index.html           two tabs: Book Appointment / Staff
  js/api.js            one request() helper for all API calls
  js/ui.js             rendering (textContent only, no innerHTML with user data)
  js/app.js            events, client-side validation, tabs
docs/
  PLAN.md  TESTING.md  AI_LOG.md  DOCUMENTATION.md
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/slots?date=YYYY-MM-DD` | 7 slots with `available` |
| POST | `/api/appointments` | Book (201 · 400 rule · 409 taken · 422 invalid) |
| GET | `/api/appointments?date=` | Day's appointments, sorted by time |
| PATCH | `/api/appointments/{id}/status` | `{"status": "Completed" \| "No-show"}` (400 if already final · 404) |
| GET | `/api/summary?date=` | Total, count per service, open slots |

All errors return `{"detail": "<friendly message>"}`.
