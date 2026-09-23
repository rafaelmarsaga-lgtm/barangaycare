# BarangayCare — Testing

**Automated:** 73 pytest tests, all passing (`cd backend` → `python -m pytest -v`).
**Manual:** 8 UI tests in the browser on a freshly seeded database, all passing.
**Clock:** automated tests pin "now" to **Thu 2026-09-24, 2:10 PM (PH time)**, so date rules
(past date, Sunday, "slot already passed today") give the same result on any day.
The API tests use an in-memory SQLite database (`DATABASE_URL=sqlite://`), so the
real `barangaycare.db` is never touched.

## 1. Automated tests (pytest)

| File | Tests | What it covers |
|------|------:|----------------|
| `tests/test_health.py` | 3 | App starts, table is created at startup, frontend is served |
| `tests/test_rules.py` | 27 | Pure business rules: slots/services lists, Sunday rule, "slot has passed", `check_bookable`, one-way status changes, `open_slots`, `build_summary` |
| `tests/test_booking_api.py` | 27 | `POST /api/appointments`, `GET /api/slots`, and friendly 422 messages |
| `tests/test_staff_api.py` | 16 | `GET /api/appointments`, `PATCH …/status`, `GET /api/summary` |
| **Total** | **73** | |

### Key test cases (instructor requirements)

| # | Requirement | Test | Input | Expected | Actual | Status |
|---|-------------|------|-------|----------|--------|--------|
| 1 | Valid booking | `test_valid_booking_is_created` | "  Maria Santos  ", 09171234567, General Check-up, Mon 2026-09-28, 09:00 | 201, name trimmed, status Booked | 201, "Maria Santos", Booked | PASS |
| 2 | No double booking | `test_same_slot_twice_is_rejected_with_409` | Same date + slot twice | 2nd → 409 "That slot is already booked. Please pick another." | 409, same message | PASS |
| 3 | Reject past dates | `test_past_date_is_rejected` | 2026-09-23 | 400 "Past dates cannot be booked." | 400, same message | PASS |
| 4 | Reject Sundays | `test_sunday_is_rejected` | 2026-09-27 | 400 "The health center is closed on Sundays." | 400, same message | PASS |
| 5 | Reject invalid contact | `test_invalid_contact_numbers_are_rejected` (6 cases) | 10 digits, 12 digits, starts 08, dashes, space, empty | 422 "Contact number must be 11 digits starting with 09." | 422, same message ×6 | PASS |
| 6 | Reject passed slot today | `test_slot_already_passed_today_is_rejected` | Today 10:00 at 2:10 PM | 400 "That time slot has already passed today." | 400, same message | PASS |
| 7 | Mark Completed | `test_booked_can_be_marked_completed` | PATCH `{"status":"Completed"}` | 200, saved as Completed | 200, Completed in list | PASS |
| 8 | Status is final | `test_final_status_cannot_be_changed_again` | Completed → No-show | 400 "Status is already final." | 400, same message | PASS |
| 9 | Daily summary | `test_summary_for_a_future_weekday` | 3 bookings: Dental ×2, Prenatal ×1 | total 3, per-service counts, open 4 | exactly that | PASS |
| 10 | Summary: Sunday | `test_summary_for_sunday_has_zero_open_slots` | 2026-09-27 | open_slots 0 | 0 | PASS |
| 11 | Summary: today after 2 PM | `test_summary_for_today_after_2pm_counts_only_later_unbooked_slots` | Today, then book 15:00 | open 1, then 0 | 1, then 0 | PASS |
| 12 | No raw Pydantic text | `test_malformed_body_never_leaks_raw_pydantic_text` | Body "not json" | 422 `{"detail": "Please check your input."}` | same | PASS |

### Full list (73)
- **test_health.py (3):** health, appointments_table_exists, frontend_is_served
- **test_rules.py (27):** seven hourly slots with lunch break · four services · Sunday is closed · Saturday is open · morning slot passed in afternoon · started slot counts as passed · later slot today not passed · future day slots ahead · past date rejected · Sunday rejected · passed slot today rejected · future slot today allowed · future Saturday allowed · Booked→Completed · Booked→No-show · Completed is final · No-show is final · open_slots lists unbooked in order · open_slots today after 2 PM · open_slots Sunday empty · summary counts with zeros · open slots future weekday · today after 2 PM = 1 · today after 2 PM with 3 PM booked = 0 · booked+passed slot not subtracted twice · Sunday = 0 open · past date = 0 open
- **test_booking_api.py (27):** valid booking · later slot today accepted · same slot twice 409 · same slot other day OK · past date 400 · Sunday 400 · passed slot today 400 · invalid contacts ×6 · exact friendly contact message · invalid names ×4 (" A ", spaces, empty, 101 chars) · missing name · invalid service · 12:00 lunch slot · invalid date · malformed body · slots mark booked unavailable · slots today after 2 PM · slots Sunday all unavailable · slots invalid date
- **test_staff_api.py (16):** list filtered + sorted · empty date → [] · list invalid date · mark Completed (persisted) · mark No-show · final status 400 · unknown id 404 · invalid status ×4 (Booked, Cancelled, completed, empty) · summary future weekday · summary counts Completed/No-show · summary Sunday · summary today after 2 PM · summary invalid date

## 2. Manual UI tests (Browser, fresh database)

Setup: delete `barangaycare.db` → `python seed_data.py` (9 sample rows) → start server.
Real date during the run: Thu 2026-09-24.

| # | Test | Steps | Expected | Actual | Status |
|---|------|-------|----------|--------|--------|
| M1 | Empty form | Click "Book appointment" with nothing filled | Inline error under each field, focus on Name | 4 errors (name, contact, service, date); focus on Name | PASS |
| M2 | Invalid contact | Contact `0917123456` (10 digits), rest valid | Inline contact error, no request sent | "Contact number must be 11 digits starting with 09." | PASS |
| M3 | Sunday | Pick 2026-09-27 | Closed message, no slots | "The health center is closed on Sundays. Please choose another day." | PASS |
| M4 | Valid booking | Lito Bautista, 09171234567, Dental, Fri 09-25, 11:00 | Taken slots disabled; confirmation card | 8/9/10 AM + 1 PM shown Unavailable; confirmation "#10 / Lito Bautista / Dental / Friday, September 25, 2026, 11:00 AM" | PASS |
| M5 | Double booking | Select 3:00 PM, another resident books it first, then submit | 409 message; slot refreshes to Unavailable | "That slot is already booked. Please pick another."; 3:00 PM → Unavailable | PASS |
| M6 | Staff list + summary | Staff tab, date 2026-09-25 | Rows sorted by time; summary matches | 6 rows 8 AM→3 PM; Total 6, Open 1/7, GC 1, Prenatal 1, Immun 1, Dental 3 | PASS |
| M7 | Status with confirmation | No-show → Esc; then Completed → "Yes, Completed" | Esc saves nothing; Yes saves; buttons removed | After Esc server still "Booked"; after Yes row shows Completed, no buttons; totals unchanged | PASS |
| M8 | History + Sunday (staff) | Dates 2026-09-23 and 2026-09-27 | Past statuses shown; Sunday empty, 0 open | Lorna: Completed, Carlo: No-show; "The health center is closed on Sundays.", Open 0/7 | PASS |

Also checked during development (Steps 5–7): a name like `<img src=x onerror=…>` is
shown as plain text (no element created, no script run); "Cannot reach the server…" when
the server is stopped, and Reload recovers; no horizontal scrolling at 375px; the staff
list reloads after a stale status click.

## 3. Refactor safety (Step 7.5)
`api.js` was refactored into a single `request()` helper. pytest: `73 passed` before and after.
Because pytest doesn't cover the frontend, a browser script made the same 14 `api.js` calls
before and after: all results and messages were identical.

## 4. Known limitations
- Tailwind is loaded from its CDN (per the exam kit, no build step). The browser prints
  "should not be used in production"; a real deployment would build the CSS with the Tailwind CLI.
- No staff login (an exam simplification stated in the plan).
- Frontend JS has no automated tests; it is covered by the manual tests above.
