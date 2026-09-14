# AI-Powered Placement Management System — Frontend

React + Vite + Tailwind CSS frontend for the Placement Management System, consuming the FastAPI backend built in Phases 2–4.

## Tech Stack

- React 18 + Vite
- Tailwind CSS
- Axios (centralized client with JWT interceptor)
- React Router v6 (protected + role-based routes)

## Setup (Windows)

```bat
cd frontend
npm install
copy .env.example .env
REM edit .env if your backend isn't at http://127.0.0.1:8000

npm run dev
```

Then open the URL Vite prints (typically `http://localhost:5173`). Make sure the backend is running first (`uvicorn app.main:app --reload` from `backend/`).

## Environment variables

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the backend API, e.g. `http://127.0.0.1:8000/api/v1`. Never hardcoded in source. |

## Project structure

```
frontend/
├── src/
│   ├── api/            # one file per backend resource; all requests go through client.js
│   ├── components/     # shared UI: Sidebar, Navbar, DataTable, Pagination, StatusBadge, ...
│   ├── context/         # AuthContext (JWT + current user), ToastContext (feedback)
│   ├── layouts/         # DashboardLayout (sidebar + navbar + content)
│   ├── routes/           # ProtectedRoute (auth + role guard)
│   └── pages/
│       ├── auth/          # Login, Register
│       ├── student/       # Dashboard, Profile, Jobs, Job details, Applications
│       ├── recruiter/      # Dashboard, Profile, Company, Jobs, Job form, Applicants, Drives
│       ├── admin/           # Dashboard, Students, Recruiters, Companies, Jobs, Applications, Audit logs
│       └── shared/           # Notifications, Unauthorized (used by more than one role)
```

## How auth/routing works

- `AuthContext` stores the JWT in `localStorage`, loads the current user via `GET /auth/me` on app start, and exposes `login`/`register`/`logout`.
- `client.js`'s response interceptor catches any `401` and logs the user out automatically, so an expired token doesn't leave the UI in a broken state.
- `ProtectedRoute` redirects to `/login` if there's no user, or to `/unauthorized` if the user's role isn't allowed on that route. Every dashboard route is wrapped in this.
- The sidebar's nav items are derived entirely from `user.role` — a student never sees admin links, etc. (This is a UX convenience, not a security boundary — the real enforcement is the backend's `require_role`.)

## ⚠️ Verification status

I could not run `npm install` or `npm run build` in the sandbox this was built in — the npm registry returned `403 Forbidden` (no network access), same restriction that blocked PyPI for the backend. What I verified instead:

- Every relative import in `src/` resolves to a real file (scripted check, 47/47 files)
- `package.json` is valid JSON
- Every page component has exactly one `export default`
- Manual review of every component for prop/hook usage correctness

**I did not verify** that `npm install` resolves all dependency versions cleanly, that Vite's JSX/Tailwind pipeline compiles without error, or that the app renders correctly in a browser. Please run:

```bat
npm install
npm run build
```

and tell me the actual output. If the build fails, paste the error and I'll fix the real cause.

## Project status

Resume upload UI, AI interview practice (question generation + answer
evaluation), and analytics dashboards (Recharts, already a dependency since
this README was first written) are now implemented across the three role
dashboards. This "Not yet implemented" note was stale — kept here as a
correction rather than silently deleted, in case your real copy of this
README has diverged with your own notes.

## Deployment (Vercel)

1. Root directory: `frontend/`
2. Build command: `npm run build`, output directory: `dist`
3. Set the `VITE_API_BASE_URL` environment variable in Vercel's project settings to your deployed backend's `/api/v1` URL
4. No other frontend-side secrets exist — the AI API key lives only in the backend's environment and is never sent to or read by this app

No deployment was performed as part of this work.
