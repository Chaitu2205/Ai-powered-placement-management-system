# AI-Powered Placement Management System — Backend

FastAPI + SQLAlchemy 2.x + MySQL backend for the AI-Powered Placement
Management System. This README covers **Phase 2**: project foundation,
database models, and Alembic migrations. Auth, business-logic APIs, and AI
features are added in later phases.

---

## Tech Stack

- Python 3.11+
- FastAPI, Uvicorn
- SQLAlchemy 2.x, Alembic
- MySQL 8.x
- Pydantic v2 / pydantic-settings

---

## 1. Install Python

Download and install Python 3.11+ from [python.org](https://www.python.org/downloads/).
During install, check **"Add python.exe to PATH"**.

Verify:

```bat
python --version
```

## 2. Create a virtual environment

From the `backend/` folder:

```bat
python -m venv venv
```

## 3. Activate the virtual environment

```bat
venv\Scripts\activate
```

Your prompt should now start with `(venv)`.

## 4. Install dependencies

```bat
pip install -r requirements.txt
```

## 5. Create the MySQL database

Open MySQL (Workbench, CLI, or any client) and run:

```sql
CREATE DATABASE placement_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'placement_user'@'localhost' IDENTIFIED BY 'placement_pass';
GRANT ALL PRIVILEGES ON placement_db.* TO 'placement_user'@'localhost';
FLUSH PRIVILEGES;
```

(Use your own username/password — just make sure they match `.env` in the next step.)

## 6. Configure environment variables

Copy the example file:

```bat
copy .env.example .env
```

Open `.env` and set real values, especially:

- `DATABASE_URL` — must match the DB/user/password created in step 5
- `JWT_SECRET_KEY` — generate one with:
  ```bat
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

`.env` is already in `.gitignore` — it must never be committed.

## 7. Run the Alembic migration

This creates every table in the database (`users`, `students`, `jobs`,
`applications`, `resumes`, `interview_sessions`, etc.):

```bat
alembic upgrade head
```

Verify tables were created:

```sql
USE placement_db;
SHOW TABLES;
```

## 8. Start the FastAPI server

```bat
uvicorn app.main:app --reload
```

You should see log output ending with something like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 9. Test the health check

```bat
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok", "message": "AI Placement Management System API is running"}
```

## 10. Open Swagger docs

In a browser, go to:

```
http://127.0.0.1:8000/docs
```

(ReDoc is also available at `/redoc`.)

---

## Alembic cheat sheet

**Create a new migration** after changing a model:

```bat
alembic revision --autogenerate -m "describe your change"
```

Always review the generated file in `alembic/versions/` before applying it —
autogenerate doesn't always catch everything (e.g. some MySQL-specific
constraint renames).

**Apply migrations:**

```bat
alembic upgrade head
```

**Roll back the last migration:**

```bat
alembic downgrade -1
```

**Roll back everything:**

```bat
alembic downgrade base
```

**Check current DB revision:**

```bat
alembic current
```

---

## Project structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, exception handlers, /health
│   ├── api/
│   │   └── v1/
│   │       └── router.py     # aggregates all /api/v1/* routers (empty until Phase 3)
│   ├── config/
│   │   └── settings.py       # pydantic-settings, reads .env
│   ├── database/
│   │   ├── base.py           # declarative Base + TimestampMixin
│   │   └── session.py        # engine, SessionLocal, get_db dependency
│   ├── models/                # SQLAlchemy ORM models (one file per table/group)
│   ├── schemas/                # Pydantic request/response models
│   ├── security/               # JWT/hashing/RBAC (implemented in Phase 3)
│   ├── services/                # business logic (implemented from Phase 4)
│   ├── ai/                       # LLM-facing layer (implemented from Phase 7)
│   └── utils/
│       └── exceptions.py     # AppException hierarchy + global error handlers
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## What's implemented in Phase 2

- Full database schema (18 tables) as SQLAlchemy 2.x models with correct
  relationships, foreign keys, unique constraints, and indexes
- A single initial Alembic migration that builds the entire schema
- Environment-based configuration (no hardcoded secrets)
- CORS configured from `CORS_ORIGINS`
- Global JSON error handling (no leaked stack traces)
- `/health` endpoint and versioned `/api/v1` prefix ready for future routers

## What's implemented in Phase 3

- Password hashing (`app/security/hashing.py`, bcrypt via passlib)
- JWT creation/verification (`app/security/jwt.py`)
- `get_current_user` and `require_role(*roles)` dependencies (`app/security/dependencies.py`)
- `POST /api/v1/auth/register` — student/recruiter only, admin rejected at the schema level
- `POST /api/v1/auth/login` — returns a JWT access token
- `GET /api/v1/auth/me` — returns the authenticated user
- Atomic `User` + `Student`/`Recruiter` profile creation (one DB transaction)
- Duplicate-email protection (409, including a race-condition-safe fallback on `IntegrityError`)
- Unit + integration tests under `tests/` (see "Running tests" below)

## Running tests

Tests run against a **separate** MySQL database so they never touch your real `placement_management` data:

```sql
CREATE DATABASE placement_management_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON placement_management_test.* TO 'placement_user'@'localhost';
FLUSH PRIVILEGES;
```

```bat
pip install -r requirements-dev.txt
pytest -v
```

`tests/conftest.py` creates every table in `placement_management_test` at the
start of the test session and drops them at the end - your real database is
never touched. Override the test DB with `TEST_DATABASE_URL` if you'd rather
use different credentials.

## Project status

All 12 phases are implemented: core placement management, authentication/RBAC,
resume upload/parsing, AI resume analysis, AI job matching, AI interview
question generation and answer evaluation, analytics dashboards, and the
Phase 12 hardening pass below.

> **Note on this README**: this copy was last actively maintained through
> Phase 3; the phase list above was stale (it still listed Phases 4–12 as
> "not yet implemented" despite all of them being merged). If your actual
> project's `README.md` has diverged from this file with your own local
> edits, treat this section and the "Deployment" section below as content to
> merge in, not a wholesale replacement — check the diff before overwriting.

## What's implemented in Phase 11 — Analytics & Dashboards

- `GET /api/v1/analytics/student` — own applications/status breakdown, open job count, up to 5 AI-matched recommended jobs, interview session/question counts, average + latest interview score, current resume's AI analysis score
- `GET /api/v1/analytics/recruiter` — own jobs posted/active/closed, applications received + status breakdown, applicants-per-job, jobs linked to a placement drive (all scoped to the recruiter's own company via SQL join, never another recruiter's data)
- `GET /api/v1/analytics/admin` — system-wide totals, applications/jobs/student-placement status breakdowns, placement percentage, last-6-months application trend
- Every metric is computed with SQL aggregation (`COUNT`/`GROUP BY`/`AVG`) — no full-table loads into Python
- **Fixed a real gap found while building this**: `Student.placement_status` was never updated anywhere in the app, meaning the admin "placement percentage" metric would have always read 0%. `application_service.update_application_status` now sets it to `selected`/`shortlisted` appropriately (never downgrades an already-selected student)
- Frontend: Student/Recruiter/Admin dashboards now pull from these endpoints instead of computing stats client-side from full lists (the recruiter dashboard previously fetched up to 100 applications just to count two status values — now the backend does that in one query). Charts via `recharts` (already a dependency since Phase 5, not newly added)

## What's implemented in Phase 12 — Security Hardening

A full review was performed against the standard checklist (auth, RBAC,
ownership, file upload, SQL injection, CORS, JWT, error handling, AI key
exposure). Most areas were already solid from earlier phases (parameterized
queries throughout via the ORM, magic-byte file validation, JWT with an
explicit algorithm allowlist, AI keys never touched by the frontend). Two
genuine issues were found and fixed:

1. **Validation-error responses could echo sensitive submitted data** — Pydantic's `RequestValidationError.errors()` includes an `"input"` key per error (the actual submitted value). A failed password-length check on `/auth/register` would echo the candidate's plaintext password straight back in the 422 response body. Fixed by stripping `"input"` from every error entry in `app/utils/exceptions.py`'s validation handler — `loc`/`msg`/`type` remain, which is everything a client needs to show a useful error.
2. **API docs were always exposed, including in a hypothetical production deployment** — `/docs`, `/redoc`, `/openapi.json` are now disabled when `APP_ENV=production`, enabled otherwise. See `app/main.py`.

**Known limitation documented, not fixed** (would require a new dependency/infrastructure decision, out of scope for a minimal hardening pass): there is no rate limiting on `/auth/login`, so this API has no built-in brute-force protection. If you deploy this publicly, consider a reverse-proxy-level rate limiter (e.g. your hosting platform's built-in one) rather than adding an in-process limiter here.

## Deployment

### Environment variables (document only — never commit real values)

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes | `mysql+pymysql://user:pass@host:port/dbname` — any MySQL-compatible managed DB (PlanetScale, Railway MySQL, AWS RDS, etc.) works |
| `JWT_SECRET_KEY` | Yes | Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`, never reuse the dev value |
| `JWT_ALGORITHM` | No | Defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to 1440 (24h) |
| `CORS_ORIGINS` | Yes | Comma-separated. Set to your real deployed frontend URL(s) — never `*` |
| `AI_API_KEY` | For AI features | Resume analysis / interview generation / evaluation return `503` cleanly if unset — the app still starts and everything else works without it |
| `AI_MODEL_NAME` | No | Defaults to `claude-sonnet-4-6` |
| `RESUME_UPLOAD_DIR` | No | Defaults to `uploads/resumes` — on most PaaS platforms this is ephemeral storage; for a real deployment, point this at (or replace resume storage with) persistent/object storage |
| `MAX_RESUME_SIZE_MB` | No | Defaults to 5 |
| `APP_ENV` | Recommended | Set to `production` to disable `/docs`/`/redoc`/`/openapi.json` (see Phase 12 above) |

### Backend — Render or Railway

1. Connect the repo, set the root directory to `backend/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set all environment variables from the table above
5. Run the migration once, either via a one-off shell/job: `alembic upgrade head`
6. Set `APP_ENV=production`

### Frontend — Vercel

1. Root directory: `frontend/`
2. Build command: `npm run build` (outputs `dist/`)
3. Set `VITE_API_BASE_URL` to your deployed backend's `/api/v1` URL (e.g. `https://your-backend.onrender.com/api/v1`)
4. Update the backend's `CORS_ORIGINS` to include your Vercel deployment URL

### Database — any MySQL-compatible managed service

- Create the database, get a connection string in `mysql+pymysql://` format
- Run `alembic upgrade head` once against it before first use (applies all 4 migrations: `0001` → `0004`)
- `alembic history` will show the full chain if you want to confirm before/after

**No deployment was performed or claimed as part of this work — the above is documentation only.**
