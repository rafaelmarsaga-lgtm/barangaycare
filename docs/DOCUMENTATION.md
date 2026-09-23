# BarangayCare — Barangay Health Center Appointment System

**Course:** IT 415 – Application Development and Emerging Technologies
**Activity:** Practice Lab Exam
**Student:** Rafael [SURNAME] · **Date:** September 24, 2026

---

## 1. System Title
**BarangayCare** — online check-up booking for the barangay health center, with no double-booked slots.

## 2. Problem Statement
The barangay health center takes check-up requests on paper. This causes long queues, and the
same time slot often gets double-booked because nobody can see which slots are already taken.
Residents need a reliable way to reserve a valid slot, and staff need a clear daily view of
who is coming and how busy the day is. The current paper process has no checking of dates,
contact numbers, or slot conflicts.

## 3. Objectives
**General Objective**
To develop a web-based appointment system that lets residents book health-center check-ups
online without double booking and lets staff manage and summarize daily appointments.

**Specific Objectives**
1. To let residents book an appointment with their name, contact number, service, date, and
   time slot, rejecting double-booked slots, past dates and times, Sundays, and invalid contact numbers.
2. To let staff view the appointments for a selected date and mark each one Completed or No-show.
3. To show a daily summary for a selected date: total appointments, count per service, and
   remaining open slots.
4. To validate all user inputs on both the server and the page, and show friendly error messages.
5. To verify the system through 73 automated tests and 8 manual UI test cases.

## 4. System Features / Requirements

| Feature | Input | Processing | Output |
|---------|-------|------------|--------|
| 1. Book Appointment (resident tab) | Name, contact number, service, date, time slot | Pydantic checks the format (name 2–100 chars, `09` + 9 digits, service and slot from fixed lists). The booking service checks the date rules (not past, not Sunday, slot not already passed today). The database UNIQUE(date, slot) constraint blocks double booking | 201 + confirmation card with reference number, or a friendly error (400/409/422). Taken slots are shown as Unavailable |
| 2. Manage Appointments (staff tab) | Selected date; Completed / No-show click + confirmation | Load that date's appointments sorted by time; PATCH the status, allowed only from Booked | List with status badges; buttons disappear once the status is final. "Status is already final." (400) or "Appointment not found." (404) on error |
| 3. Daily Summary (staff tab) | Selected date | Count all appointments that date, group by the 4 services; open slots = unbooked AND still bookable (0 on Sundays and past dates, only future slots today) | Cards: Total, Open slots out of 7, one card per service (zeros shown) |

**Validation & error handling**
| Input | Rule | Error shown |
|-------|------|-------------|
| Name | Required, trimmed, 2–100 characters | "Name must be 2–100 characters." |
| Contact number | Exactly 11 digits, starts with 09 (no spaces/dashes) | "Contact number must be 11 digits starting with 09." |
| Service | One of General Check-up, Prenatal, Immunization, Dental | "Please choose a valid service." |
| Date | Valid date | "Please choose a valid date." |
| Date | Not before today | "Past dates cannot be booked." |
| Date | Not a Sunday | "The health center is closed on Sundays." |
| Time slot | One of 8, 9, 10, 11 AM, 1, 2, 3 PM | "Please choose a valid time slot." |
| Time slot | If today, must not have started yet | "That time slot has already passed today." |
| Date + slot | Not already booked | "That slot is already booked. Please pick another." (409) |
| Status (staff) | Only Completed or No-show | "Invalid status." |
| Status (staff) | Current status must be Booked | "Status is already final." |
| Appointment id | Must exist | "Appointment not found." (404) |

All errors use one shape, `{"detail": "<message>"}`; a custom handler replaces raw Pydantic
validation text with the friendly messages above.

**Instructor requirement → where it's met**
| Requirement | Where satisfied |
|-------------|-----------------|
| Residents book with name, contact, service, date, slot | Feature 1 · `POST /api/appointments`, booking tab |
| Prevent double booking of the same slot | UNIQUE(appointment_date, time_slot) in `models.py` → 409 |
| Reject past dates | `check_bookable()` in `services/booking.py` → 400 |
| Reject Sundays | `is_closed_day()` / `check_bookable()` → 400 |
| Reject invalid contact numbers | `ContactNumber` pattern in `schemas.py` → 422, plus the page's own check |
| Staff view appointments for a selected date | Feature 2 · `GET /api/appointments?date=`, staff tab |
| Staff mark Completed / No-show | `PATCH /api/appointments/{id}/status` with one-way rule |
| Daily summary: total, per service, open slots | Feature 3 · `GET /api/summary?date=` |
| At least 3 test cases | 73 automated + 8 manual (see `docs/TESTING.md`) |
| Documentation of AI usage | `docs/AI_LOG.md` (every step) and section 6 below |

## 5. Technology / AI Tools Used
| Layer | Technology |
|-------|-----------|
| Frontend | HTML, vanilla JavaScript (ES modules, fetch/async-await), Tailwind CSS via CDN |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 |
| Database | SQLite (local file `backend/barangaycare.db`) |
| Testing | pytest + FastAPI TestClient on in-memory SQLite (73 tests) |
| Editor | Claude Code desktop app |
| AI tools | Claude Code (desktop app) with Superpowers (brainstorming, writing-plans, test-driven-development), UI UX Pro Max (design system), and the Impeccable design checks. The Frontend Design skill was not installed in this session, so it was not used. |

## 6. AI Prompt & Output Evidence
Workflow followed: PROMPT → AI OUTPUT → MY ANALYSIS → MODIFICATION → TESTING → FINAL RESULT

### 6.1 System Planning
- **AI tool:** Claude Code desktop app (Plan mode, brainstorming + writing-plans skills)
- **Purpose:** Turn the instructor's scenario into a plan before any code exists.
- **Prompt:** [SCREENSHOT]
- **AI output:** [SCREENSHOT] 4 clarifying questions, then `docs/PLAN.md` (objectives, 3 IPO features, data model, validation table, API, requirement mapping, 8 checkpoints).
- **My analysis / what I used or changed:** Answered the 4 questions (reject passed slots today, one-way status, allow repeat contact numbers, one page with two tabs). Then required three changes: a Step 7.5 refactor checkpoint, friendly 422 messages instead of raw Pydantic text, and "open slots" meaning unbooked AND still bookable instead of 7 − booked.
- **Result:** Approved plan with 8 checkpoints + 7.5, followed step by step with a commit after each.

### 6.2 Code Generation
- **AI tool:** Claude Code · **Purpose:** Build each checkpoint test-first (TDD) for the business rules and APIs.
- **Prompt:** [SCREENSHOT] "Proceed to Step N" · **AI output:** [SCREENSHOT]
- **What I used/changed:** Asked for an inline confirmation before Completed/No-show (added in Step 7) after the AI pointed out a mis-click can't be undone.
- **Test result:** Every step shown RED (failing) first, then GREEN; final suite `73 passed`.

### 6.3 Debugging
| Problem | Prompt | AI Response | Fix | Test Result |
|---------|--------|-------------|-----|-------------|
| New staff endpoints returned 404/405 on the live server while tests passed | [SCREENSHOT] | Checked the server log: "Reloading..." never finished, so the old code was still running. The code was fine | Restarted the server; no code change | Live: list 200, re-mark 400, unknown id 404 — PASS |
| Staff error box always visible (empty pink box) | [SCREENSHOT] | Tailwind's `flex` class overrides the browser's `[hidden]` rule | Added `[hidden]{display:none!important}` | No hidden element visible — PASS |
| Page scrolled sideways on phones with a long name | [SCREENSHOT] | A `1fr` grid column can't shrink below its longest word | `minmax(0,1fr)` + `overflow-wrap:anywhere` | Page width = screen width at 375px — PASS |
| Staff row stayed "Booked" after a failed status update | [SCREENSHOT] | Server data had changed (another staff member marked it); page showed old data | Reload the list after an error, then show the message | Row shows real status + "Status is already final." — PASS |

### 6.4 Refactoring
| Before | AI Prompt | After | Test Result |
|--------|-----------|-------|-------------|
| `api.js`: 5 functions each repeating fetch + offline + JSON + error handling (72 lines, 5 fetch calls) [SCREENSHOT] | [SCREENSHOT] "Proceed to Step 7.5" | One `request(method, path, body)` helper; each endpoint is one line (34 lines, 1 fetch call) [SCREENSHOT] | 73 passed before → 73 passed after; 14/14 api.js calls identical in a before/after browser check |

**Why this refactor:** The same error handling was copied five times, so a fix (for example
adding a timeout) would have had to be made in five places and could easily be missed in one.

### 6.5 Documentation / Testing
- **AI tool:** Claude Code · **Purpose:** Write TESTING.md, README, this document; final fresh run.
- **Prompt:** [SCREENSHOT] · **AI output:** [SCREENSHOT]
- **What I used/changed:** [Fill in: what you reviewed or edited in these documents.]

### Responsible AI use
- No passwords, API keys, or personal data were included in prompts; all names in the app are sample data.
- Every AI output was read, run, and tested before being accepted (tests + Browser checks at every step).
- Example of a correction: the AI's first plan counted open slots as "7 − booked". I changed
  it so passed slots and Sundays don't count as open, because staff would otherwise see slots
  that nobody can actually book.

## 7. Testing Results
| Test | Description | Input | Expected Result | Actual Result | Status |
|------|-------------|-------|-----------------|---------------|--------|
| 1 | Valid input | Maria Santos, 09171234567, General Check-up, Mon 2026-09-28, 9:00 AM | 201 Created, status Booked | 201, Booked, name trimmed | PASS |
| 2 | Invalid input | Contact `0912345678` (10 digits) | 422 "Contact number must be 11 digits starting with 09." | Same message | PASS |
| 3 | Edge case | Same date + slot booked twice | 409 "That slot is already booked. Please pick another." | Same message | PASS |
| 4 | Edge case | Sunday 2026-09-27 | 400 "The health center is closed on Sundays." | Same message | PASS |
| 5 | Edge case | Past date 2026-09-23 | 400 "Past dates cannot be booked." | Same message | PASS |
| 6 | Edge case | Summary on Sunday / today after 2 PM | Open slots 0 / only 3 PM open | 0 / 1 | PASS |

Automated suite: `73 passed` — [SCREENSHOT of pytest output]
Full tables (all 73 tests + 8 manual UI tests): `docs/TESTING.md`.

## 8. Final System Screenshots
1. [SCREENSHOT] Home / booking tab
2. [SCREENSHOT] Feature 1 in use: booking confirmation card
3. [SCREENSHOT] Feature 2 in use: staff list with confirmation ("Mark as No-show?")
4. [SCREENSHOT] Feature 3 in use: daily summary cards
5. [SCREENSHOT] Validation error message (invalid contact / slot already booked)
6. [SCREENSHOT] Mobile view

## Lessons Learned
*(Draft from the AI log — rewrite in your own words.)*
- AI did well: writing tests first made the date rules (Sunday, passed slots, open slots) easy to prove with a fixed clock.
- AI got wrong: a variable name was reused in the same block, and the error box stayed visible because of a CSS conflict. Both were caught by checking in the browser, not by the tests.
- I'd do differently: [Fill in.]
