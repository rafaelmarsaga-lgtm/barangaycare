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

## Step 2 — Business rules, TDD (2026-09-24)
- **Asked:** "Proceed to Step 2": pure booking/status/summary rules, tests first.
- **AI produced:** `tests/test_rules.py` (24 tests on a fixed clock, Thu 2026-09-24 14:10 PH); `services/booking.py` (`SLOTS`, `SERVICES`, `BookingError`, `is_closed_day`, `slot_has_passed`, `check_bookable`, `can_change_status`); `services/summary.py` (`build_summary`, `count_open_slots`).
- **Decisions:** a slot that has already started counts as passed (14:00 at 14:10 cannot be booked); open slots reuse `is_closed_day` + `slot_has_passed`, and an extra test guards against subtracting a booked-and-passed slot twice.
- **Test result:** RED `24 failed` (NotImplementedError stubs) → GREEN `27 passed` (full suite).

## Step 3 — Booking API + friendly validation errors (2026-09-24)
- **Asked:** "Proceed to Step 3": POST /api/appointments, GET /api/slots, schemas, and a RequestValidationError handler returning `{"detail": "<friendly message>"}`.
- **AI produced:** `schemas.py` (constrained Name/ContactNumber types, Literal service/slot, `FRIENDLY_MESSAGES`), `routers/appointments.py` (BookingError → 400, IntegrityError → 409), `routers/slots.py`, 422 handler in `main.py`, `open_slots()` shared by slots + summary, 30 new tests.
- **Changes vs. plan:** `now_ph` is used directly as the injectable "now" dependency, brought forward from Step 4 (the booking endpoint needs it too). No "is it free?" SELECT before insert: the UNIQUE constraint is the single check.
- **Test result:** RED `30 failed` (405 / NotImplementedError) → GREEN `57 passed`. Live curl: 201 then 409 on the same slot; bad contact → 422 friendly message; Sunday → 400. The first live call returned 405 because the auto-reloader was still restarting, not a code bug.

## Step 4 — Staff API + daily summary (2026-09-24)
- **Asked:** "Proceed to Step 4": list appointments by date, PATCH status, GET summary.
- **AI produced:** `GET /api/appointments?date=` (sorted by slot), `PATCH /api/appointments/{id}/status` (404 / 400 "Status is already final."), `routers/summary.py` using `build_summary` + injectable `now_ph`; 16 new tests incl. Sunday = 0 open and today-after-2 PM.
- **Debugging:** live curl gave 404/405 while tests passed. Server logs showed "StatReload detected changes … Reloading..." with no "Started server process", so the old process was still serving. Root cause: the uvicorn reload hung, not the code. Fix: restarted the server; all endpoints then correct.
- **Test result:** RED `16 failed` → GREEN `73 passed`. Live: list 200, Completed 200, re-mark 400, id 999 → 404, summary Mon `total 2, open 5`, Sunday `open 0`.

## Step 5 — Resident "Book Appointment" tab (2026-09-24)
- **Asked:** "Proceed to Step 5": booking UI with the ui-ux-pro-max skill.
- **AI produced:** `index.html` (two ARIA tabs, form, slot radio grid, success card, info sidebar), `js/api.js` (fetch + friendly/offline errors), `js/ui.js` (textContent-only rendering, slot grid, skeleton), `js/app.js` (tabs with arrow keys, client validation mirroring the server, 409 → reload slots). Design system from ui-ux-pro-max: "Accessible & Ethical" style, blue #1E40AF + green, Atkinson Hyperlegible, 44px targets; skipped its "Enterprise Gateway" landing-page pattern (wrong fit for a form).
- **Browser checks:** empty submit → 4 inline errors + focus on Name; Sunday → closed message; Monday slots match DB; 10-digit contact → inline error; valid booking → confirmation #3; slot taken via curl behind the UI → 409 alert + slot refreshed to Unavailable; XSS name `<img onerror=…>` shown as text, no element created; desktop two-column layout OK.
- **False alarm:** a selected slot looked unselected in one screenshot; computed style showed the blue background was applied, so it was a screenshot taken before repaint, not a bug.
- **Test result:** backend suite still `73 passed`; no JS console errors (only the browser's log of the intentional 409).
