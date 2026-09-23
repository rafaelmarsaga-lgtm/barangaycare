# BarangayCare — Project Plan

## Context
IT 415 timed lab exam (~3 h total, ~2 h of building). The instructor's scenario: a barangay
health center books check-ups on paper, which leads to long queues and double-booked slots.
The goal is a working localhost system that Rafael can explain line by line. The build
follows CLAUDE.md: Kit A, one checkpoint at a time, TDD for business logic, and a git
commit plus an AI_LOG entry after each step.

## Decisions from the clarifying questions (answered 2026-09-24)
| Question | Decision |
|---|---|
| Past time slots on today | **Rejected** (400). If it is 2:10 PM, today's 8:00–2:00 slots can't be booked |
| Status changes | **One-way**: Booked → Completed or No-show; changing a final status → 400 |
| Same contact, several slots in one day | **Allowed**; the only rule is one appointment per slot |
| Layout | **One page, two tabs**: "Book Appointment" and "Staff" |

**Defaults I picked (minor):** "today" and "now" use Philippine time, a fixed UTC+8 with no DST.
I used a fixed offset because `zoneinfo` on Windows would need the extra `tzdata` package.
Names are trimmed before checking their length. The contact number must be exactly 11 digits;
spaces and dashes are rejected rather than stripped, so what's stored is what was validated.
A No-show still occupies its slot, per CLAUDE.md: open = 7 − appointments that day.

---

## 1. System title & problem statement
**BarangayCare — Barangay Health Center Appointment System**

The barangay health center takes check-up requests on paper. This causes long queues, and the
same time slot often gets double-booked. Residents need a reliable way to reserve a valid
slot, and staff need a clear daily view of who is coming.

## 2. Objectives
**General:** To develop a web-based appointment system that lets residents book health-center
check-ups online without double booking and lets staff manage and summarize daily appointments.

**Specific:**
1. To let residents book an appointment with their name, contact number, service, date, and
   time slot. Double-booked slots, past dates and times, Sundays, and invalid contact numbers
   are rejected.
2. To let staff view the appointments for a selected date and mark each one Completed or No-show.
3. To show a daily summary for a selected date: total appointments, count per service, and
   remaining open slots.

## 3. Major features (Input → Processing → Output)
| # | Feature | Input | Processing | Output |
|---|---|---|---|---|
| F1 | **Book Appointment** (resident tab) | Name, contact no., service, date, time slot | Pydantic checks the format (name length, `09`+9 digits, service/slot from the fixed lists). The booking service checks the date rules (not past, not Sunday, slot not already passed today). The DB unique constraint on (date, slot) blocks double booking | 201 + confirmation card, or a friendly error (400/409/422). The slot picker shows taken slots as disabled |
| F2 | **Manage Appointments** (staff tab) | Selected date; a "Completed"/"No-show" button click | Fetch that date's appointments sorted by slot; PATCH the status, allowed only from Booked | Table of appointments with status badges; the buttons disappear once the status is final. 404 if the ID is unknown, 400 for an invalid transition |
| F3 | **Daily Summary** (staff tab) | Selected date | Count all appointments that date, group them by the 4 services, open = 7 − total | Cards: Total, one per service (zeros shown), Open slots |

## 4. Data model (SQLite, one table)
**`appointments`**
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | autoincrement |
| name | VARCHAR(100) | trimmed, 2–100 chars |
| contact_number | VARCHAR(11) | `^09\d{9}$` |
| service | VARCHAR(30) | one of the 4 services |
| appointment_date | DATE | |
| time_slot | VARCHAR(5) | one of `08:00 09:00 10:00 11:00 13:00 14:00 15:00` |
| status | VARCHAR(10) | `Booked` (default) / `Completed` / `No-show` |
| created_at | DATETIME | set from a single `now_ph()` helper |

**Constraint:** `UNIQUE(appointment_date, time_slot)`. The database itself enforces "one
appointment per slot", so two simultaneous requests can't both succeed. The losing insert
raises IntegrityError, which is returned as 409.
*Why one table:* services, slots, and statuses are fixed lists, so separate lookup tables would
add joins without adding anything we need (YAGNI).

## 5. Validation rules (every user input)
| Input | Rule | Layer | Status | Message shown |
|---|---|---|---|---|
| Name | required, trimmed, 2–100 chars | Pydantic | 422 | "Name must be 2–100 characters." |
| Contact | exactly 11 digits, starts with 09 | Pydantic regex | 422 | "Contact number must be 11 digits starting with 09." |
| Service | one of the 4 services | Pydantic Literal/Enum | 422 | "Please choose a valid service." |
| Date | valid YYYY-MM-DD | Pydantic | 422 | "Please choose a valid date." |
| Date | not before today (PH) | booking service | 400 | "Past dates cannot be booked." |
| Date | not a Sunday | booking service | 400 | "The health center is closed on Sundays." |
| Time slot | one of the 7 slots | Pydantic | 422 | "Please choose a valid time slot." |
| Time slot | if the date is today, the slot start time must still be ahead | booking service | 400 | "That time slot has already passed today." |
| Date+slot | not already taken | DB unique constraint | 409 | "That slot is already booked. Please pick another." |
| Status (staff) | only `Completed` or `No-show` | Pydantic | 422 | "Invalid status." |
| Status (staff) | current status must be `Booked` | booking service | 400 | "Status is already final." |
| Appointment id | must exist | router | 404 | "Appointment not found." |
| Query `date` (staff/summary/slots) | valid date | FastAPI query type | 422 | "Please choose a valid date." |

The UI repeats the simple checks (required fields, contact pattern, `min=today` on the date
picker) so users get feedback instantly. The server remains the authority. All user text is
rendered with `textContent`.

**Why the date rules live in a service and not in Pydantic:** they depend on "now". A pure
function that takes `now` as a parameter can be unit-tested for "today at 2 PM" or "a Sunday"
without faking the clock.

## 6. Stack
**Kit A (full-stack)**: appointments must be saved, checked against each other for double
booking, and shared between resident and staff views, so they need a server and a database
rather than one browser's localStorage.
FastAPI + Pydantic + SQLAlchemy + SQLite, and vanilla JS + Tailwind CDN served by FastAPI.
Tests use pytest + TestClient on in-memory SQLite (StaticPool). No other dependencies.

## 7. API
| Method | Path | Purpose | Codes |
|---|---|---|---|
| GET | `/api/slots?date=` | 7 slots, each with `available` (false if taken or already past) | 200, 400, 422 |
| POST | `/api/appointments` | create booking | 201, 400, 409, 422 |
| GET | `/api/appointments?date=` | list for date, sorted by slot | 200, 422 |
| PATCH | `/api/appointments/{id}/status` | `{status}` | 200, 400, 404, 422 |
| GET | `/api/summary?date=` | `{date, total, by_service:{4 keys}, open_slots}` | 200, 422 |

`/api/slots` is a small extra that makes F1 friendlier (disabled taken slots). If time runs
short, it's the first thing to cut; the 409 message still protects the rule.

## 8. Instructor requirement → where it's met
| Requirement | Feature / Step |
|---|---|
| Residents book with name, contact, service, date, slot | F1 · Steps 3 + 5 |
| Prevent double booking of the same slot | F1 unique constraint → 409 · Steps 1, 3 (test) |
| Reject past dates | F1 booking service → 400 · Steps 2, 3 (tests) |
| Reject Sundays | F1 booking service → 400 · Steps 2, 3 (tests) |
| Reject invalid contact (11 digits, starts 09) | F1 Pydantic → 422 · Step 3 (tests) + UI check Step 5 |
| Staff view appointments for a selected date | F2 · Steps 4 + 6 |
| Staff mark Completed / No-show | F2 · Steps 2, 4 + 6 |
| Daily summary: total, per service, open slots | F3 · Steps 2, 4 + 6 |
| At least 3 test cases | ~20 automated pytest cases (Steps 1–4) + manual table in TESTING.md · Step 8 |
| Documentation of AI usage | `docs/AI_LOG.md` updated every step; filled template · Step 8 |

## 9. Scope
Nothing in the scenario needs cutting; it fits about 2 h. **Deliberately out of scope**
(stated openly): staff login (per CLAUDE.md), cancel/reschedule, editing a booking,
SMS reminders, holidays, pagination.
**If time runs short, cut in this order:** (1) `/api/slots` availability display,
(2) Step 7 polish beyond loading/empty/error states.

---

## 10. Checkpoints (≈ 2 h of building)

Each step: build → run the tests/app → show output → commit `Step N: …` → append to AI_LOG → **stop**.

### Step 1 — Scaffold, database, health check (~10 min)
- **Build:** folder layout from CLAUDE.md; `requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic, pytest, httpx);
  `database.py` (engine, `SessionLocal`, `Base`, `get_db`); `models.py` (`Appointment` + unique constraint);
  `main.py` (lifespan creates tables, `GET /api/health`, static mount of `frontend/`);
  `tests/conftest.py` (in-memory SQLite, StaticPool, `get_db` override, `with TestClient(app) as client`);
  placeholder `frontend/index.html`.
- **Verify:** `python -m pytest -v` → `test_health` passes. `python -m uvicorn app.main:app --reload`,
  then open http://127.0.0.1:8000/api/health → `{"status":"ok"}`, and `/` serves the placeholder page.

### Step 2 — Business rules, TDD, pure functions (~20 min)
- **Build:** `services/booking.py` with `SLOTS`, `SERVICES`, `now_ph()`,
  `check_bookable(date, slot, now) -> None` (raises `BookingError`),
  `can_change_status(current, new) -> bool`, `slot_has_passed(date, slot, now) -> bool`;
  `services/summary.py` with `build_summary(date, appointments) -> dict`.
- **Tests first** (`tests/test_rules.py`): past date rejected; Sunday rejected; today with a passed slot rejected;
  today with a future slot OK; future Saturday OK; Booked→Completed OK; Completed→No-show rejected;
  summary counts per service with zeros filled in and open = 7 − total.
- **Verify:** show the tests failing first (RED), then all of them passing (GREEN) in the pytest output.

### Step 3 — Booking API (~20 min)
- **Build:** `schemas.py` (`AppointmentCreate`, `AppointmentOut`, `StatusUpdate`, `SlotOut`, `SummaryOut`);
  `routers/appointments.py` with `POST /api/appointments`; `routers/slots.py` with `GET /api/slots`.
  IntegrityError → 409; BookingError → 400.
- **Tests** (`tests/test_booking_api.py`): valid booking 201; same slot twice 409; past date 400;
  Sunday 400; contact `0912345678` (10 digits) 422; contact `08123456789` 422; name `" A "` 422;
  slots endpoint marks the booked slot unavailable.
- **Verify:** pytest all green; a manual `curl` POST against the running server shows 201, then 409.

### Step 4 — Staff API + summary (~15 min)
- **Build:** `GET /api/appointments?date=`, `PATCH /api/appointments/{id}/status`, `routers/summary.py` `GET /api/summary?date=`.
- **Tests** (`tests/test_staff_api.py`): list is filtered by date and sorted by slot; mark Completed 200;
  re-mark 400; unknown id 404; invalid status 422; summary after 3 bookings (2 services) returns the right counts and open = 4.
- **Verify:** pytest all green (≈20 tests); curl `/api/summary` output shown.

### Step 5 — Resident "Book Appointment" tab (~20 min)
- **Build:** `index.html` (Tailwind CDN, header, two tabs, booking form); `js/api.js` (fetch wrappers that turn
  error responses into readable messages); `js/ui.js` (render helpers, `textContent` only); `js/app.js` (tab switch,
  load slots when the date changes, submit handler). Use the `ui-ux-pro-max` / `frontend-design` skills for styling.
- **Verify in the Browser pane:** a valid booking shows a confirmation; rebooking that slot shows it disabled/409 message;
  a Sunday shows the closed message; a bad contact shows an inline error. Loading state appears while fetching.

### Step 6 — Staff tab: list, status buttons, summary (~20 min)
- **Build:** date picker (defaults to today), summary cards, appointments table (cards on mobile), Completed/No-show
  buttons that refresh the list and summary; empty state ("No appointments for this date").
- **Verify in the Browser pane:** the bookings from Step 5 appear; marking one Completed updates its badge and removes
  its buttons; summary numbers match the table; picking an empty date shows the empty state.

### Step 7 — Seed data + polish (~10 min)
- **Build:** `seed_data.py` (clears and inserts ~8 sample appointments across the next few open days, skipping Sundays);
  error banner when the server is unreachable; check the layout at ~375 px width.
- **Verify:** `python seed_data.py` prints the count; the app shows the seeded data; mobile-width screenshot in the Browser pane.

### Step 8 — Documentation + final check (~10 min)
- **Build:** `docs/TESTING.md` (table of the automated tests + 5 manual UI tests with expected/actual results);
  complete `docs/AI_LOG.md`; README run instructions; fill the relevant parts of `DOCUMENTATION_TEMPLATE.md` (text only, screenshots are Rafael's).
- **Verify:** fresh run: `python seed_data.py` → uvicorn → click through both tabs → `python -m pytest -v`, then show the final pass count.

## Review focus (risky inputs; each has a test in the step named)
1. Server date vs. PH date around midnight → `now_ph()` is injected into `check_bookable` (Step 2).
2. Two bookings for the same slot → DB unique constraint + 409 test (Steps 1, 3).
3. A whitespace-only or 1-letter name after trimming → 422 test (Step 3).
4. A contact number with a dash, space, or 10/12 digits → 422 test (Step 3).
5. Changing a status that's already final, or a nonexistent id → 400/404 tests (Step 4).

## Verification (end-to-end)
`cd backend` → `python -m pytest -v` (all pass) → `python seed_data.py` →
`python -m uvicorn app.main:app --reload` → http://127.0.0.1:8000/. Book a slot, try the same slot again,
try a Sunday and a bad contact number, then on the Staff tab mark Completed and check the summary.
