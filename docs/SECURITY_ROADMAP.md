# Kuntolaskuri security roadmap

A phased checklist for hardening Kuntolaskuri before it stores personal or health data.
Each item is tagged with the security concept it teaches:
**OWASP** = OWASP Top 10 2021 category, **GDPR** = article, **CIA** = confidentiality / integrity / availability.
Tick items off in the PR that completes them.

---

## Findings in current code (verified)

What is already good:
- All SQL uses SQLAlchemy `text()` with bound parameters (`kuntolaskuri/users.py`, `kuntolaskuri/tests.py`), so no SQL injection was found.
- Passwords are hashed with Werkzeug `generate_password_hash` (PBKDF2-SHA256 by default in Werkzeug 2.3) (`users.py: register`).
- User-scoped queries filter by `session["user_id"]`, not by an id from the request (`users.py`).
- The `dockerfile` creates and runs as a non-root `appuser`.
- There is a hand-rolled CSRF token on some forms (`users.py: login`, templates).

Issues:
- [ ] **F1 Hard-coded DB credentials** `postgres/postgres` in `docker-compose.yml` (db env + `DATABASE_URL`) in a public repo. *OWASP A05/A07, CIA-C*
- [ ] **F2 `SECRET_KEY` is never set.** `__init__.py` reads `getenv("SECRET_KEY")` but compose doesn't provide it, so it is `None`. No fail-fast check. *OWASP A02/A05*
- [ ] **F3 Database port published** (`5433:5432` in `docker-compose.yml`). *OWASP A05, attack surface*
- [ ] **F4 Dev mode in deployment:** `FLASK_ENV: development` in compose, `app.run(debug=True)` in `app.py`, `flask run` dev server in `dockerfile` CMD, and the source dir mounted over `/app` (`.:/app`). *OWASP A05*
- [ ] **F5 No CSRF check** on `/test_page` POST, `/login`, `/sign-up`; `/logout` is a GET (forced-logout CSRF). Token comparison uses `!=`, not `secrets.compare_digest` (`routes.py`). *OWASP A01*
- [ ] **F6 No `login_required`.** Protected routes access `session["user_id"]` / `session["csrf_token"]` directly, so anonymous requests crash with `KeyError` → HTTP 500 instead of 401 (e.g. `/user_page/delete`, `/test_history`, `/result_page`, `/logout`). *OWASP A01/A04, CIA-A*
- [ ] **F7 Unvalidated index** in `/test_history` POST: `int(request.form["result_date"])` used as list index; non-numeric or out-of-range → 500, negative values index from the end. *OWASP A03/A04*
- [ ] **F8 Session handling:** session is not cleared on login (only individual keys added), logout `del`s keys and fails if one is missing; test results are stored in Flask's client-side cookie session (signed, *not* encrypted, so readable by anyone holding the cookie). No cookie `Secure`/`SameSite` config. *OWASP A07, CIA-C*
- [ ] **F9 Weak password policy:** no minimum length, maximum 32 characters (`routes.py: sign_up`); no login rate limiting or lockout. *OWASP A07*
- [ ] **F10 Account deletion is incomplete/buggy:** `DELETE_USER` deletes results and the user but not `user_info`; `user_info.user_id` FK has no `ON DELETE CASCADE` (`init.sql`), so deletion fails when profile info exists. *GDPR Art. 17, CIA-I*
- [ ] **F11 Schema lacks constraints:** no `NOT NULL` on `username`/`password`/`user_id`, no `UNIQUE` on `user_info.user_id`, `sex`/`age` unconstrained in DB (`init.sql`). *CIA-I*
- [ ] **F12 Bare `except:`** hides errors (`users.py: register, get_information`; `routes.py: result_page`). *OWASP A09*
- [ ] **F13 Outdated pins / broken healthcheck:** Flask 2.3.2, Werkzeug 2.3.6, Jinja2 3.1.2 etc. are old (run `pip-audit`); `dockerfile` HEALTHCHECK imports `requests`, which isn't in `requirements.txt`, so it always fails. *OWASP A06*
- [ ] **F14 Personal data stored in plaintext** (`user_info`: first/last name, age, sex; `user_results`). Fine for now, must be addressed before health data. *GDPR Art. 9/32*

---

## Phase 1 — Secrets & configuration
- [ ] Move all credentials to `.env` (git-ignored) + `.env.example`; compose uses `env_file`. *OWASP A05*
- [ ] Generate a strong `SECRET_KEY` (`python -c "import secrets;print(secrets.token_urlsafe(48))"`); app refuses to start without it. *OWASP A02*
- [ ] Rotate the DB password (old one is in git history forever). *CIA-C*
- [ ] Store deploy secrets in GitHub Actions Secrets / environments. *OWASP A05*
- [ ] Enable GitHub secret scanning + push protection. *DevSecOps*
- **Learning exercise:** run `gitleaks detect` or `trufflehog git file://.` on the repo and explain why deleting a secret in a new commit isn't enough.

## Phase 2 — Authentication & sessions
- [ ] Switch hashing to argon2id (`argon2-cffi`), rehash on next login. *OWASP A02/A07*
- [ ] Password policy: min 12 chars, allow long passphrases, check against breached lists (HIBP k-anonymity). *OWASP A07, NIST 800-63B*
- [ ] Rate-limit login/sign-up (Flask-Limiter). *OWASP A07, CIA-A*
- [ ] `session.clear()` on login and logout; logout becomes POST. *OWASP A07 (session fixation)*
- [ ] Cookie flags: `HttpOnly`, `Secure`, `SameSite=Lax`; session lifetime limit. *OWASP A07*
- [ ] Optional: TOTP 2FA. *Defense in depth*
- **Learning exercise:** decode your Flask session cookie with `flask-unsign --decode` and observe that it is readable but tamper-proof — explain signing vs encryption.

## Phase 3 — Access control
- [ ] `login_required` decorator on every user route/API endpoint (401, not 500). *OWASP A01*
- [ ] Every query scoped by authenticated user id; results fetched by owned record id, not list index. *OWASP A01 (IDOR)*
- [ ] Framework-wide CSRF (Flask-WTF `CSRFProtect`), `compare_digest`. *OWASP A01*
- [ ] Negative pytest tests: user A can't read/modify/delete user B's data. *OWASP A01*
- **Learning exercise:** create two accounts and try to access user B's results as user A (change ids/params in Burp or DevTools); write the test that proves it fails.

## Phase 4 — Input & output (SQLi, XSS)
- [ ] Keep ORM/bound parameters only; add bandit rule check in CI. *OWASP A03*
- [ ] Schema validation (pydantic/marshmallow) for every API payload; reject unknown fields. *OWASP A03/A04*
- [ ] Rely on Jinja2/React auto-escaping; ban `|safe`/`innerHTML` with user data. *OWASP A03 (XSS)*
- [ ] Content-Security-Policy, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors` (Flask-Talisman). *OWASP A05*
- [ ] Generic error pages; no stack traces to users. *OWASP A05*
- **Learning exercise:** try `' OR 1=1 --` and `<script>alert(1)</script>` in every field; explain why each fails (or fix it if it doesn't).

## Phase 5 — Transport & encryption at rest
- [ ] HTTPS only via Cloudflare Tunnel; HSTS header. *OWASP A02, CIA-C*
- [ ] DB reachable only on the internal Docker network. *Attack surface*
- [ ] Encrypt health fields at application level (e.g. `cryptography` Fernet / pgcrypto) with key outside the DB. *GDPR Art. 32, OWASP A02*
- [ ] Full-disk encryption (LUKS) on the server; encrypted, tested backups. *GDPR Art. 32, CIA-C/A*
- **Learning exercise:** dump the DB with `pg_dump` and compare what an attacker sees with and without field encryption.

## Phase 6 — Privacy / GDPR
- [ ] Data inventory: what is stored, why, legal basis (explicit consent for health data). *GDPR Art. 5, 6, 9, 30*
- [ ] Explicit, granular consent before storing health data; withdrawable. *GDPR Art. 7, 9(2)(a)*
- [ ] Data export (JSON) endpoint. *GDPR Art. 15, 20*
- [ ] Complete account deletion incl. `user_info` (fix F10, `ON DELETE CASCADE`). *GDPR Art. 17*
- [ ] Retention policy + scheduled purge of inactive accounts. *GDPR Art. 5(1)(e)*
- [ ] Privacy notice in Finnish & English; camera/mic processed locally only, stated clearly. *GDPR Art. 13, 25*
- [ ] Minimize fields (e.g. drop first/last name if not needed). *GDPR Art. 5(1)(c), 25*
- **Learning exercise:** write a one-page DPIA (GDPR Art. 35) for the camera rep-counting feature.

## Phase 7 — DevSecOps
- [ ] Dependabot for pip, Docker and GitHub Actions. *OWASP A06*
- [ ] CodeQL workflow on PRs. *OWASP A03/A04*
- [ ] `bandit` and `pip-audit` in CI; fail on high severity. *OWASP A06*
- [ ] Local Ollama reviewer agent comments on every PR (self-hosted runner). *Shift-left*
- [ ] Branch protection on `main`: PR + passing checks required. *CIA-I*
- [ ] Pin Actions by commit SHA; least-privilege `permissions:` in workflows. *OWASP A08 (supply chain)*
- [ ] Self-hosted runner only for private repo or trusted PRs (never run fork PRs on it). *OWASP A08*
- **Learning exercise:** intentionally commit a vulnerable snippet on a branch and see which tool (CodeQL, bandit, reviewer agent) catches it.

## Phase 8 — Infrastructure hardening (Ubuntu server)
- [ ] `ufw` default deny incoming; allow SSH from LAN/Tailscale only. *Attack surface*
- [ ] SSH: keys only (`PasswordAuthentication no`, `PermitRootLogin no`). *OWASP A07*
- [ ] `fail2ban` for SSH. *CIA-A*
- [ ] `unattended-upgrades` for security patches. *OWASP A06*
- [ ] Docker: non-root containers, read-only FS where possible, no `.:/app` mount in prod, gunicorn instead of dev server, `restart: unless-stopped`, resource limits. *OWASP A05*
- [ ] Remove DB port mapping (fix F3). *Attack surface*
- [ ] Runner runs as a dedicated unprivileged user. *Least privilege*
- **Learning exercise:** run `nmap -sV SERVER_IP` from the Mac before and after hardening and document the difference; run `lynis audit system`.

## Phase 9 — Logging & monitoring
- [ ] Structured logs of security events (login success/fail, deletion, export) with user id only — no health/personal data. *OWASP A09, GDPR Art. 32*
- [ ] Audit log table for access to health data. *GDPR Art. 30, CIA-I*
- [ ] Local log-watcher agent summarizes errors daily; alert on login-failure spikes. *OWASP A09*
- [ ] Log rotation and retention limit. *GDPR Art. 5(1)(e)*
- **Learning exercise:** brute-force your own login with a small script and verify the logs + rate limit catch it.

## Phase 10 — Threat modeling (STRIDE)
- [ ] Draw a data-flow diagram: browser (camera/mic) → Cloudflare → Flask → Postgres, plus GitHub Actions runner.
- [ ] For each element list STRIDE threats: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege; map each to a control or roadmap item.
- [ ] Re-do threat model whenever a feature touches health data.
- **Learning exercise:** complete the STRIDE table in `docs/THREAT_MODEL.md` (e.g. with OWASP Threat Dragon) and discuss one threat you accept and why.

## Phase 11 — Self-pentest exercises
- [ ] Run OWASP ZAP baseline scan against a local instance. *OWASP A05*
- [ ] Manual tests with Burp Suite: IDOR, CSRF, XSS, SQLi, session fixation, forced browsing. *OWASP A01/A03/A07*
- [ ] Tamper with client-sent rep counts / fitness levels; confirm server re-validates. *OWASP A04, CIA-I*
- [ ] Brute-force/credential-stuffing test against rate limiting. *OWASP A07*
- [ ] Write a short pentest report: finding, severity (CVSS), fix, retest. *Professional practice*
- **Learning exercise:** reproduce findings F5–F7 before fixing them, then write the pytest that proves each fix.
