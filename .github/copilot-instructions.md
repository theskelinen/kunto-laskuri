# Copilot instructions — Kuntolaskuri

## Project context
Kuntolaskuri is a fitness test web app (squat, sit-up, arm lift, balance, shoulder mobility) that
scores users into fitness classes 1–5 using Toimia reference values. The UI is Finnish.
It is being refactored from server-rendered Flask into a JSON API + modern frontend, with
in-browser camera rep counting (MediaPipe Pose) and voice counting (Web Speech API).
The app may store personal and health data (GDPR Art. 9 special category). Treat all user data as sensitive.
The owner is a cyber security student: code must be secure AND teach the reasoning behind it.

## Stack
- Python 3.11, Flask, Flask-SQLAlchemy / SQLAlchemy 2.x, PostgreSQL, Docker Compose
- Tests: pytest. Deployed via self-hosted GitHub Actions runner, exposed through Cloudflare Tunnel.
- Planned: JSON API under `/api/v1`, separate frontend; MediaPipe + Web Speech run client-side only.

## Security non-negotiables (never violate; refuse and explain instead)
1. **No secrets in code or compose files.** Read config from environment / `.env` (git-ignored). Provide `.env.example` with placeholders. Fail fast at startup if `SECRET_KEY` or `DATABASE_URL` is missing.
2. **SQL only via ORM or bound parameters** (`text()` with `:params`). Never build SQL with f-strings, `%` or `+`.
3. **Authorization on every user-scoped resource.** Every query for user data filters by the authenticated user's id from the session/token, never by an id from the request. Use a `login_required` decorator; unauthenticated → 401/redirect, not 500.
4. **CSRF protection** on every state-changing request (Flask-WTF `CSRFProtect` or SameSite cookies + token for the API). State changes never via GET (including logout). Compare tokens with `secrets.compare_digest`.
5. **Validate all input server-side** (type, range, length, allow-lists). Use a schema (pydantic/marshmallow) for the API. Never trust client-computed fitness levels or rep counts without range checks.
6. **Passwords hashed with argon2id** (`argon2-cffi`) or bcrypt; enforce min length 12, no low max length. Add login rate limiting (Flask-Limiter). Generic error messages for login failures.
7. **Never log health data, personal data, passwords, tokens or session contents.** Log user ids and event types only.
8. **Data minimization.** Do not add new personal/health fields without a stated purpose in the PR. Prefer age range over birth date, etc.
9. **Camera and microphone data are processed in the browser only and never uploaded or stored.** Only derived numbers (rep counts) may be sent to the server, and only with user action.
10. **Output encoding.** Never use `|safe`, `Markup()` or `innerHTML`/`dangerouslySetInnerHTML` with user data.
11. **Secure session config:** `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE` (prod), `SESSION_COOKIE_SAMESITE="Lax"`; clear the session on login and logout. Don't store sensitive data in Flask's client-side cookie session.
12. **Production:** no `debug=True`, no Flask dev server (use gunicorn), DB port not published, containers run as non-root.
13. **Dependencies:** pin versions, prefer maintained libraries, no new dependency without a reason in the PR.

## Testing requirements
- Every change ships with pytest tests (`tests/`), using a test DB/fixtures — never real user data.
- Security-relevant changes need a negative test: e.g. user A cannot read/delete user B's results,
  missing CSRF token → 400/403, unauthenticated → 401, invalid input → 400.
- CI must pass: pytest, bandit, pip-audit, CodeQL. Do not disable or skip checks to make CI green.

## Coding conventions
- PEP 8, type hints on new code, small functions; business logic outside route handlers.
- No bare `except:`; catch specific exceptions and return proper HTTP status codes.
- Database changes via migrations (Flask-Migrate/Alembic), with `NOT NULL`, FKs and `ON DELETE CASCADE` where appropriate.
- UI strings stay Finnish (keep them in one place to allow translation); code, comments and docs in English.
- Keep commits focused; one concern per PR.

## Pull request descriptions (required)
The owner is learning security. Every PR description must include:
- **What & why** — the change in plain language.
- **Security reasoning** — threats considered, which control addresses them, and the related
  concept (e.g. OWASP Top 10 2021 category, GDPR article, CIA property).
- **Tests** — what was tested, including negative/abuse cases.
- **Roadmap link** — which item in `docs/SECURITY_ROADMAP.md` it ticks off, if any.
