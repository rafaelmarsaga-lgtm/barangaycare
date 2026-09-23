# AI Usage Log — BarangayCare

## Step 0 — Planning (2026-09-24)
- **Asked:** Plan the system from the instructor's scenario (brainstorming + writing-plans skills), no code yet; clarifying questions in one batch.
- **AI produced:** 4 clarifying questions, then `docs/PLAN.md`: title/problem statement, objectives, 3 features (IPO), one-table data model with UNIQUE(date, slot), validation table, API, requirement→step mapping, 8 checkpoints.
- **My decisions/changes:** Chose to reject passed time slots for today, one-way status changes (Booked → Completed/No-show), allow the same contact number to book several slots a day, and a one-page two-tab layout.
- **Test result:** N/A (planning only).

## Step 0b — Plan review changes (2026-09-24)
- **Asked:** Three changes to the approved plan: add a Step 7.5 refactor checkpoint, add a friendly-message `RequestValidationError` handler, and redefine open slots as "unbooked AND still bookable".
- **AI produced:** Updated `docs/PLAN.md`: the Step 7.5 refactor checkpoint with before/after test runs; the Step 3 handler plus exact-message tests; `is_closed_day()` shared by booking and summary; `build_summary(date, appointments, now)`; new Step 2/4 tests for today after 2 PM, Sunday = 0 and past date = 0; `/api/slots` aligned with the same rule.
- **My decisions/changes:** Overrode the CLAUDE.md default of "open = 7 − booked", because counting a passed or closed slot as "open" would mislead staff.
- **Test result:** N/A (planning only).

## Step 1 — Scaffold, database, health check (2026-09-24)
- **Asked:** "Proceed to Step 1": folder layout, DB engine/session, Appointment model, lifespan, health endpoint, static frontend, test setup.
- **AI produced:** `database.py` (DATABASE_URL env var, StaticPool for in-memory), `models.py` (UNIQUE(appointment_date, time_slot)), `main.py` (lifespan create_all, `/api/health`, static mount), `now_ph()` in `services/booking.py`, `conftest.py`, 3 tests, placeholder `index.html`, `.claude/launch.json`.
- **Changes vs. plan:** tests switch the DB with `DATABASE_URL=sqlite://` instead of overriding `get_db`, so lifespan creates tables on the test DB and no real `.db` file is touched. `now_ph()` was created now (needed by `created_at`), not in Step 2.
- **Test result:** RED first (ModuleNotFoundError), then `3 passed`; live server `/api/health` → `{"status":"ok"}`, `/` → 200.
