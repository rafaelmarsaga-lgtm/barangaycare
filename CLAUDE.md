# CLAUDE.md — IT 415 Lab Exam Project

> Standing instructions for Claude Code. This copy is filled in for the
> practice drill: Barangay Health Center Appointment System.

## Who I am and what this is
- I'm Rafael, a BSIT student taking a timed (~3 hour) lab exam in IT 415
  (Application Development and Emerging Technologies).
- I must build a small working system from my instructor's scenario, run it on
  localhost, and explain every part of it in a Q&A.
- Project: **BarangayCare — Barangay Health Center Appointment System**
- Stack chosen: **Kit A (full-stack)**, because appointments must be stored,
  checked for double booking, and shared between residents and staff.

## Scenario defaults (use these instead of asking me)
- Time slots: hourly, 8:00, 9:00, 10:00, 11:00 AM and 1:00, 2:00, 3:00 PM
  (7 slots per day). One appointment per slot.
- Open days: Monday to Saturday. Sundays are closed.
- Services: General Check-up, Prenatal, Immunization, Dental.
- Contact number: exactly 11 digits, starts with 09.
- Name: required, 2–100 characters.
- Status: Booked (default) → Completed or No-show.
- Bookings allowed from today onward; past dates are rejected.
- Staff side: no login for this exam. A simple "Staff" page is enough,
  stated openly as an exam simplification.
- Daily summary counts all appointments for the selected date;
  open slots = 7 minus appointments booked that day.

## How we work (non-negotiable)
1. **Checkpoint-driven.** Do ONE step at a time. When a step is done, stop,
   summarize what changed, tell me how to verify it, and wait for me to type
   "Proceed to Step N". Never build several steps in one go.
2. **Plan before code.** For anything bigger than a small fix, outline the
   approach first so I can catch a wrong direction before code exists.
3. **Verify, don't claim.** Before saying something works, run it (tests, the
   server, a curl/request) and show me the actual output. If you could not run
   something, say so plainly.
4. **Explain decisions briefly.** One or two sentences on *why* for each design
   choice, so I can defend it. No long essays.
5. **Stay in scope.** Build what the scenario asks. If you think something extra
   is worth adding, suggest it — don't just add it.
6. **Never delete or weaken a test to make it pass.** Fix the code, or tell me
   the test is wrong and why.
7. **No new dependencies** beyond the kit below without asking me first.

## Skills to use
- Planning: `superpowers:brainstorming` then `superpowers:writing-plans`.
  Time is short: ask all clarifying questions in ONE batch (max 5).
- Building: `superpowers:test-driven-development` for business logic.
- Bugs: `superpowers:systematic-debugging` — find the root cause before fixing.
- Finishing a step: `superpowers:verification-before-completion`.
- UI: `ui-ux-pro-max` and `frontend-design`.
- Do NOT use git worktrees or subagent-driven development — work inline in
  this folder. Plain git commits are fine and wanted.

## Stack kits

### Kit A — Full-stack (default for "system" scenarios with records/users)
- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy, SQLite (local file)
- Frontend: HTML + vanilla JS (fetch/async-await) + Tailwind CSS via CDN, no build step
- FastAPI serves the frontend as static files (one origin, no CORS)
- Tests: pytest + FastAPI TestClient on an in-memory SQLite DB
  - Always use `with TestClient(app) as client:` so startup/lifespan runs
    (otherwise tables aren't created → "no such table").
  - Use `StaticPool` + `check_same_thread=False` for in-memory SQLite in tests.
- Use the `lifespan` handler, not `@app.on_event`. Use timezone-aware or a
  single `utcnow()` helper, not `datetime.utcnow`.

```
project/
  backend/
    app/
      main.py          # app, lifespan, routers, static mount
      database.py      # engine, session, Base
      models.py        # SQLAlchemy models
      schemas.py       # Pydantic request/response models + validation
      routers/         # one file per feature
      services/        # business logic (pure, testable)
    tests/
    seed_data.py
    requirements.txt
  frontend/
    index.html
    js/api.js  js/ui.js  js/app.js
  docs/
    PLAN.md  TESTING.md  AI_LOG.md
```
Run: `cd backend` → `python seed_data.py` → `python -m uvicorn app.main:app --reload`
→ open http://127.0.0.1:8000/  ·  Tests: `python -m pytest -v`

### Kit B — Lightweight (for "website" / small tool scenarios, no server needed)
- Single folder: `index.html`, `js/logic.js` (pure functions), `js/storage.js`
  (localStorage wrapped in try/catch), `js/app.js` (DOM), Tailwind via CDN.
- Business logic lives in `logic.js` with no DOM access so it can be tested.
- Tests: `node --test` on `logic.js` if Node is installed; otherwise a manual
  test table in docs/TESTING.md.
- Run: `python -m http.server 8000` → open http://127.0.0.1:8000/

## Code rules
- Validate every input on the server (Pydantic) AND give friendly messages in
  the UI. Return proper status codes: 400 bad request, 404 not found,
  409 duplicate, 422 validation.
- Insert user text into the page with `textContent`, never `innerHTML` with
  raw user data (XSS).
- No hardcoded secrets, passwords, or API keys. If auth is needed, hash
  passwords with PBKDF2 from `hashlib` (salted).
- Keep functions small, names clear, comments explain *why* not *what*.
- Frontend must be responsive and show loading, empty, and error states.
- After UI changes, check the running app in the Browser pane before saying
  it looks right.

## Git
- `git init` at the start. Commit after each verified checkpoint with a clear
  message, e.g. `Step 3: add booking validation + tests`.

## Logging for my documentation
After each step, append 3–5 lines to `docs/AI_LOG.md`:
step, what I asked, what you produced, what I changed/rejected, test result.
