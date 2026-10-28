# Kuntolaskuri – Infrastructure Guide

Practical, step-by-step setup for the **laptop workshop** (staging, security lab, CI runner, local AI agents) and the **cloud production server**. Commands are copy-pasteable; replace `ALL_CAPS` placeholders.

> Items marked **(verify)** depend on your plan, provider offers, or versions that change over time. Check them before relying on them.

---

## 1. Overview

**Golden rule: real user / health data lives only in production. The laptop gets fake or test data only.**

| Machine | Role |
|---|---|
| Mac | Your desk: editor, Copilot, SSH client |
| Ubuntu laptop ("workshop") | Staging copy of the app, security lab, self-hosted GitHub Actions runner, local Ollama agents |
| Cloud VPS (e.g. DigitalOcean droplet) | Production: real users, real data, HTTPS, backups |
| GitHub | Code, CI (GitHub-hosted runners), Secrets, PR reviews |

```mermaid
flowchart LR
    Mac["Mac<br/>VS Code + Copilot"] -- "git push" --> GH["GitHub repo<br/>Actions + Secrets"]
    Mac -- "SSH (key only)" --> Runner

    subgraph Laptop["Ubuntu laptop (workshop) - NO real data"]
        Runner["Self-hosted runner"]
        Ollama["Ollama<br/>qwen2.5-coder:7b / llama3.2:3b"]
        Staging["Staging app<br/>Docker Compose + fake data"]
        Lab["Security lab<br/>ZAP, nmap, sqlmap"]
    end

    GH -- "PR review job" --> Runner
    Runner --> Ollama
    Runner -- "PR comment (gh)" --> GH
    GH -- "deploy via SSH deploy key<br/>(only when CI passes on main)" --> Proxy
    Lab -- "attacks" --> Staging

    subgraph Cloud["Cloud VPS (production)"]
        Proxy["Caddy / Cloudflare Tunnel<br/>HTTPS"]
        Web["Flask + gunicorn"]
        DB[("PostgreSQL<br/>internal only")]
        Proxy --> Web --> DB
    end

    Users["Users (browser)"] -- "https://YOUR_DOMAIN" --> Proxy
    DB -- "encrypted backups" --> Backup[("Off-site storage")]
```

Flow: develop on the Mac, then push a branch and open a PR. CI (pytest, bandit, pip-audit on GitHub-hosted runners) and the local reviewer check it, and the staging app on the laptop is where you test and attack it. When you merge to `main` and CI is green, the change deploys to the cloud.

---

## 2. Laptop base hardening

Run these on the laptop (over SSH from the Mac).

### 2.1 Updates and automatic security updates
```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades     # answer "Yes"
systemctl status unattended-upgrades --no-pager
sudo unattended-upgrade --dry-run --debug           # optional: see what it would do
```

### 2.2 Firewall (ufw)
Allow SSH **before** enabling, or you lock yourself out. Check your LAN subnet with `ip a` (e.g. `192.168.1.0/24`).
```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp     # SSH, LAN only (adjust subnet)
sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp   # staging app, LAN only
sudo ufw enable
sudo ufw status verbose
```
> ⚠️ **Docker bypasses ufw** for published ports, because it writes its own iptables rules. Bind published ports to a specific IP or localhost (see §3), and never publish the database port.

### 2.3 SSH: keys only, no passwords
Your Mac key already works. Confirm it first:
```bash
# On the Mac
ssh USER@LAPTOP_IP 'echo key login OK'
```
Then on the laptop:
```bash
sudo tee /etc/ssh/sshd_config.d/99-hardening.conf >/dev/null <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
MaxAuthTries 3
X11Forwarding no
AllowUsers YOUR_USERNAME
CONF
sudo sshd -t && sudo systemctl reload ssh
```
Keep your current session open and test a **new** SSH login from the Mac before you log out. Also make sure no earlier file in `/etc/ssh/sshd_config.d/` sets `PasswordAuthentication yes`, because the first value wins: `grep -ri passwordauth /etc/ssh/sshd_config /etc/ssh/sshd_config.d/`.

### 2.4 fail2ban
```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local >/dev/null <<'CONF'
[sshd]
enabled  = true
backend  = systemd
maxretry = 5
findtime = 10m
bantime  = 1h
CONF
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

### 2.5 Keep running with the lid closed
```bash
sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/lid.conf >/dev/null <<'CONF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
CONF
sudo systemctl restart systemd-logind
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```
Restarting logind can end a local console session, but SSH stays up. Keep the laptop plugged in, and limit the battery charge in the BIOS if it supports that **(verify)**.

### 2.6 tmux (long jobs survive SSH disconnects)
```bash
sudo apt install -y tmux
tmux new -s work        # start a session
# Ctrl+b then d          -> detach
tmux attach -t work     # reattach later
```

### 2.7 Quick checks
```bash
sudo ss -tulpn                                   # what is listening? Only expected ports.
last -n 10
sudo journalctl -u ssh --since today | tail
```

---

## 3. Docker + running the app as staging

### 3.1 Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
less get-docker.sh                   # read scripts before running them (good habit)
sudo sh get-docker.sh
sudo usermod -aG docker $USER        # then log out and back in
docker run --rm hello-world
docker compose version
```
> 🔐 Being in the `docker` group is effectively **root**. Only trusted users belong there.

### 3.2 Clone and create `.env`
```bash
mkdir -p ~/apps && cd ~/apps
git clone https://github.com/theskelinen/kunto-laskuri.git && cd kunto-laskuri
umask 077
cat > .env <<ENVFILE
POSTGRES_USER=kunto
POSTGRES_PASSWORD=$(openssl rand -hex 24)
POSTGRES_DB=kuntolaskuri_db
SECRET_KEY=$(openssl rand -hex 32)
ENVFILE
umask 022
grep -qxF '.env' .gitignore 2>/dev/null || echo '.env' >> .gitignore
cat .env    # check it
```
Commit a `.env.example` with **placeholder** values only, and never the real `.env`. The app already reads `SECRET_KEY` and `DATABASE_URL` from the environment (`kuntolaskuri/__init__.py`).

### 3.3 Staging compose file
The repo's current `docker-compose.yml` hard-codes `postgres/postgres`, publishes `5433:5432`, runs `FLASK_ENV: development` and bind-mounts the source. Fixing that is roadmap item F1. A safer version looks like this (the repo's Dockerfile is named `dockerfile` in lowercase):

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:13            # keep 13 for now; upgrading needs a dump/restore (verify)
    env_file: .env
    # NO "ports:" -> the database is reachable only inside the compose network
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./kuntolaskuri/fitness_data.csv:/docker-entrypoint-initdb.d/fitness_data.csv:ro
      - ./kuntolaskuri/balance_mobility.csv:/docker-entrypoint-initdb.d/balance_mobility.csv:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      retries: 5
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: dockerfile
    env_file: .env
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    ports:
      - "LAPTOP_LAN_IP:5000:5000"   # staging on LAN only; use "127.0.0.1:5000:5000" behind a proxy
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```
Compose reads `.env` automatically for the `${...}` substitution.

### 3.4 Run it
```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web          # Ctrl+C stops following
```
Then open `http://LAPTOP_IP:5000` on the Mac.

Useful commands:
```bash
docker compose down                          # stop (keeps data)
docker compose down -v                       # stop AND delete the DB volume (fresh start; init.sql runs again)
git pull && docker compose up -d --build     # update staging
docker compose exec db psql -U kunto -d kuntolaskuri_db
```
Note that the init scripts only run on an **empty** volume. If you change the DB user or password, run `docker compose down -v` once.

Put **fake** users and results only in staging (for example from the test-data agent in §4).

---

## 4. Local AI agents (Ollama)

### 4.1 Ollama as a service
The official install script already creates a systemd service.
```bash
systemctl status ollama --no-pager
sudo systemctl enable --now ollama
ollama list                          # expect qwen2.5-coder:7b and llama3.2:3b
ss -tlnp | grep 11434                # expect 127.0.0.1:11434
```
Keep the API local-only. **Do not** set `OLLAMA_HOST=0.0.0.0`, because the API has no authentication.

Performance on the i5-1135G7 without a GPU: the 3B model is fairly quick, and the 7B model gives roughly 5–10 tokens/s, so a review takes 1–3 minutes.

### 4.2 Reviewer script `~/bin/review.sh`
```bash
mkdir -p ~/bin
cat > ~/bin/review.sh <<'SH'
#!/usr/bin/env bash
# Usage: review.sh [BASE]   (default HEAD~1). Run inside the repo.
set -euo pipefail
BASE=${1:-HEAD~1}
MODEL=${REVIEW_MODEL:-qwen2.5-coder:7b}
DIFF=$(git diff "$BASE" -- . ':!*.csv' | head -c 20000)
[ -z "$DIFF" ] && { echo "No changes."; exit 0; }
PROMPT="You are a strict code reviewer for a Flask + PostgreSQL app that may store health data.
Review this diff. List only real problems: bugs, security issues (secrets, SQL injection, XSS,
missing auth/CSRF, debug mode), missing tests, unclear code.
For each: file, line, problem, fix. If it looks fine, say LGTM.

$DIFF"
ollama run "$MODEL" "$PROMPT"
SH
chmod +x ~/bin/review.sh

cd ~/apps/kunto-laskuri && ~/bin/review.sh HEAD~1     # review the last commit
~/bin/review.sh main                                   # compare the current branch with main
```
Its output is advisory. Small models miss real bugs and invent fake ones, so treat it as a second pair of eyes, never as a security gate.

### 4.3 Other agents (same pattern)
| Agent | Model | How |
|---|---|---|
| Docs / translator | `llama3.2:3b` | `ollama run llama3.2:3b "Update this README section to match this diff: $(git diff main -- '*.py' \| head -c 15000)"`, or translate FI↔EN UI strings |
| Log watcher | `llama3.2:3b` | Daily cron job, see below |
| Study buddy | `llama3.2:3b` | Interactive `ollama run llama3.2:3b`: "Explain CSRF using this code: …", "Quiz me on OWASP A01 Broken Access Control" |
| Test-data generator | `qwen2.5-coder:7b` | `ollama run qwen2.5-coder:7b "Generate 50 fake users and test results as SQL INSERTs for this schema: $(cat init.sql)"` |

Log watcher example (staging only):
```bash
cat > ~/bin/logwatch.sh <<'SH'
#!/usr/bin/env bash
cd ~/apps/kunto-laskuri
LOGS=$(docker compose logs --since 24h --no-color 2>&1 | tail -c 15000)
ollama run llama3.2:3b "Summarise errors, warnings and suspicious activity (failed logins, scans, bursts of 4xx/5xx) in these logs. Be brief.

$LOGS" > ~/logwatch-$(date +%F).txt
SH
chmod +x ~/bin/logwatch.sh
( crontab -l 2>/dev/null; echo "0 7 * * * $HOME/bin/logwatch.sh" ) | crontab -
```
> Never copy production logs that hold personal or health data to the laptop. Use the log watcher on staging, or anonymise logs first.

---

## 5. Self-hosted GitHub Actions runner

### 5.1 ⚠️ Security first
A self-hosted runner **executes code from the repo on your laptop.** Your repo is **public**, so anyone can open a PR from a fork. If a workflow runs fork code on your runner, that person gets a shell on your machine and your network. GitHub recommends self-hosted runners only for private repos **(verify current docs)**.

Rules:
1. Untrusted code (tests, builds) runs on **GitHub-hosted** runners. The self-hosted job only reads the diff and calls Ollama.
2. The self-hosted job runs only for PRs **from the same repo** (the `if:` guard below). Never use `pull_request_target` together with a checkout of PR code.
3. In **Settings → Actions → General**, require approval for fork PR workflows from all outside collaborators **(verify the wording in the current UI)**.
4. Run the runner as a dedicated, unprivileged Linux user that is **not** in `sudo` and **not** in the `docker` group.
5. Give jobs the least-privilege `GITHUB_TOKEN` (`permissions:` per job).
6. The simplest fix of all is making the repo **private**, which removes the fork risk.

### 5.2 Install as a service
In GitHub, go to **Repo → Settings → Actions → Runners → New self-hosted runner → Linux x64**. That page shows the **current** download URL, version, SHA-256 and a one-time token. Copy those; `X.Y.Z` below is a placeholder.
```bash
sudo adduser --disabled-password --gecos "" ghrunner
sudo -iu ghrunner bash -c '
  mkdir -p actions-runner && cd actions-runner &&
  curl -o runner.tar.gz -L https://github.com/actions/runner/releases/download/vX.Y.Z/actions-runner-linux-x64-X.Y.Z.tar.gz &&
  echo "SHA256_FROM_PAGE  runner.tar.gz" | sha256sum -c &&
  tar xzf runner.tar.gz &&
  ./config.sh --url https://github.com/theskelinen/kunto-laskuri --token TOKEN_FROM_PAGE \
              --name laptop --labels laptop,ollama --unattended'
cd /home/ghrunner/actions-runner
sudo ./svc.sh install ghrunner
sudo ./svc.sh start
sudo ./svc.sh status
```
The runner needs `git` and the GitHub CLI `gh` (`sudo apt install -y gh`, **verify** that your Ubuntu release packages it, otherwise use GitHub's apt repo from cli.github.com). It reaches Ollama on `127.0.0.1:11434`. Install the reviewer for the runner user:
```bash
sudo install -o ghrunner -g ghrunner -m 755 ~/bin/review.sh /home/ghrunner/review.sh
```

### 5.3 `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  test-and-scan:
    runs-on: ubuntu-latest          # GitHub-hosted: untrusted code runs here, not on the laptop
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U test" --health-interval 5s --health-retries 10
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test_db
      SECRET_KEY: ci-only-not-a-secret
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt pytest bandit pip-audit
      - name: Tests
        run: pytest -q             # add a tests/ folder first; pytest exits with code 5 if no tests exist
      - name: Bandit (static security scan)
        run: bandit -r kuntolaskuri app.py -ll
      - name: pip-audit (known-vulnerable dependencies)
        run: pip-audit -r requirements.txt

  local-review:
    needs: test-and-scan
    # Same-repo PRs only, NEVER forks:
    if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository
    runs-on: [self-hosted, laptop, ollama]
    timeout-minutes: 20
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run local reviewer
        run: |
          ~/review.sh "origin/${{ github.base_ref }}" > review.txt 2>&1 || true
          { echo "### 🤖 Local reviewer (qwen2.5-coder:7b) – advisory only"; echo; cat review.txt; } > comment.md
      - name: Post PR comment
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: gh pr comment ${{ github.event.pull_request.number }} --body-file comment.md
```
Note that `pip-audit` will probably flag the currently pinned old versions (Flask 2.3.2, Werkzeug 2.3.6 and so on). That's expected, and a good first fix. Also pin actions to commit SHAs for supply-chain safety, and turn on **Dependabot**, **CodeQL** and **secret scanning** in Settings → Code security.

---

## 6. Production cloud server

### 6.1 Create the server
- Use DigitalOcean credit from the Student Pack. The amount and duration change, so **verify** them on the pack page. Azure for Students is an alternative.
- Droplet: Ubuntu LTS, and a 1–2 GB RAM plan is enough to start **(verify price)**. Pick an EU region (Frankfurt or Amsterdam) for GDPR. Use **SSH key authentication** by pasting your Mac's `~/.ssh/id_ed25519.pub`, and turn on the provider's cloud firewall allowing 22 (only your IP if possible), 80 and 443.
- Health data is GDPR special-category data, so read the provider's DPA and data-location terms **(verify)**.

### 6.2 Harden it
Do the same as §2 (updates, unattended-upgrades, ufw, keys-only SSH, fail2ban), but first create your own user:
```bash
# as root, first login only
adduser YOUR_USERNAME && usermod -aG sudo YOUR_USERNAME
rsync --archive --chown=YOUR_USERNAME:YOUR_USERNAME ~/.ssh /home/YOUR_USERNAME
# log in as YOUR_USERNAME in a new terminal, then apply §2.3 (PermitRootLogin no)
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable
```
Skip the lid switch step, and don't install Ollama or a runner on production.

### 6.3 Docker + gunicorn
Install Docker as in §3.1. Then make the app production-ready in the repo:
```bash
echo "gunicorn==23.0.0" >> requirements.txt     # verify the latest version on PyPI
```
In `dockerfile`, replace the `CMD`:
```dockerfile
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
```
`app:app` works because `app.py` runs `app = create_app()`. The `debug=True` in `app.py` only applies under `python app.py`, so never start production that way, and never set `FLASK_DEBUG=1`. The Dockerfile's `HEALTHCHECK` imports `requests`, which isn't in `requirements.txt`, so fix it or use `python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')"`.

Create `docker-compose.prod.yml` for the production differences, for example publishing web to localhost only:
```yaml
services:
  web:
    ports: !override
      - "127.0.0.1:5000:5000"
```
(`!override` needs Docker Compose v2.24+ **(verify)**. Otherwise keep a separate full prod compose file.)

### 6.4 HTTPS: pick ONE

**Option A: Caddy (automatic Let's Encrypt certificates).** Add it to `docker-compose.prod.yml`:
```yaml
services:
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    restart: unless-stopped
volumes:
  caddy_data:
```
`Caddyfile`:
```
YOUR_DOMAIN {
    reverse_proxy web:5000
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }
}
```
Caddy reaches `web` over the compose network, so `web` doesn't need published ports at all.

**Option B: Cloudflare Tunnel (no inbound web ports).** Create a tunnel in the Cloudflare Zero Trust dashboard under Networks → Tunnels **(verify menu names)** and copy its token. Then:
```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run
    environment:
      TUNNEL_TOKEN: ${CF_TUNNEL_TOKEN}
    restart: unless-stopped
```
In the dashboard, set the public hostname's service to `http://web:5000`. You can then close 80 and 443 in ufw and the cloud firewall. Turn on "Always Use HTTPS" and HSTS in Cloudflare.

### 6.5 Domain and DNS
- Free first-year domain from the Student Pack (Namecheap, Name.com or .TECH): **verify** the current offer and the renewal price after year 1. Otherwise expect about €10–15 a year.
- With Caddy, add an **A record** `YOUR_DOMAIN → DROPLET_IP` (plus `AAAA` for IPv6) and check it with `dig +short YOUR_DOMAIN`.
- With Cloudflare Tunnel, point the domain's nameservers to Cloudflare. The tunnel creates the DNS record.

### 6.6 Secrets
- On the server, keep `/opt/kunto/.env` (`chmod 600`) with **new** values. The old `postgres/postgres` is public in git history, so never reuse it.
- In GitHub, use **Settings → Environments → `production`** with yourself as required reviewer and deployments limited to `main`. Its secrets are `PROD_HOST`, `PROD_SSH_KEY` and `PROD_KNOWN_HOSTS`.
- Never echo secrets in workflow logs, and never commit `.env`.

### 6.7 Deploy workflow (SSH with a dedicated deploy key)
Create a key used **only** for deploys:
```bash
# On the Mac
ssh-keygen -t ed25519 -f ~/.ssh/kunto_deploy -N "" -C "github-deploy"
ssh-keyscan -t ed25519 DROPLET_IP      # output -> PROD_KNOWN_HOSTS secret
cat ~/.ssh/kunto_deploy                # -> PROD_SSH_KEY secret
cat ~/.ssh/kunto_deploy.pub            # -> server authorized_keys below
```
On the server, create a deploy user without sudo. It's in the docker group, which is still powerful, so the key is locked to one command:
```bash
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/kunto && sudo chown deploy:deploy /opt/kunto
sudo -iu deploy git clone https://github.com/theskelinen/kunto-laskuri.git /opt/kunto
sudo -iu deploy bash -c 'mkdir -p ~/.ssh && chmod 700 ~/.ssh'
echo 'command="/home/deploy/deploy.sh",restrict ssh-ed25519 AAAA...PUBLIC_KEY github-deploy' \
  | sudo -u deploy tee -a /home/deploy/.ssh/authorized_keys
sudo sed -i 's/^AllowUsers .*/& deploy/' /etc/ssh/sshd_config.d/99-hardening.conf && sudo sshd -t && sudo systemctl reload ssh
```
`/home/deploy/deploy.sh` stays outside the repo, so a commit can't change what the key runs:
```bash
sudo -u deploy tee /home/deploy/deploy.sh >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/kunto
git fetch origin main && git reset --hard origin/main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker image prune -f
SH
sudo chmod 700 /home/deploy/deploy.sh
```
`.github/workflows/deploy.yml`:
```yaml
name: Deploy
on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]
permissions:
  contents: read
jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.event == 'push'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy over SSH
        env:
          KEY: ${{ secrets.PROD_SSH_KEY }}
          KNOWN: ${{ secrets.PROD_KNOWN_HOSTS }}
          HOST: ${{ secrets.PROD_HOST }}
        run: |
          mkdir -p ~/.ssh && chmod 700 ~/.ssh
          printf '%s\n' "$KEY" > ~/.ssh/id_ed25519 && chmod 600 ~/.ssh/id_ed25519
          printf '%s\n' "$KNOWN" > ~/.ssh/known_hosts
          ssh deploy@"$HOST"      # the forced command runs deploy.sh
```
The deploy job deliberately runs on a GitHub-hosted runner. Even if the laptop were compromised, the key can only redeploy `main`.

### 6.8 Encrypted Postgres backups
Generate an [age](https://github.com/FiloSottile/age) key pair **on the Mac** and keep the private key off the server:
```bash
# Mac
brew install age && age-keygen -o ~/kunto-backup.key     # note the "Public key: age1..."
```
On the server (as `deploy`):
```bash
sudo apt install -y age
sudo mkdir -p /var/backups/kunto && sudo chown deploy:deploy /var/backups/kunto
sudo -u deploy tee /home/deploy/backup.sh >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/kunto
set -a; source .env; set +a
F=/var/backups/kunto/db-$(date +%F_%H%M).sql.gz.age
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip | age -r AGE_PUBLIC_KEY > "$F"
find /var/backups/kunto -name '*.age' -mtime +14 -delete
SH
sudo chmod 700 /home/deploy/backup.sh
sudo -u deploy bash -c '( crontab -l 2>/dev/null; echo "30 3 * * * /home/deploy/backup.sh" ) | crontab -'
```
- Copy the backups **off the server** (for example `rclone` to DigitalOcean Spaces or another EU bucket). They're already encrypted. Droplet snapshots or backups are an extra layer **(verify price)**.
- **Test restores** monthly into a throwaway database on the server, for example a temporary container. Real data must not land on the laptop.
  `age -d -i kunto-backup.key FILE.age | gunzip | docker exec -i RESTORE_CONTAINER psql -U USER -d restore_test`
- At-rest disk encryption by the provider is usually on **(verify)**. Encrypt sensitive health fields at application level as well (see the security roadmap).

### 6.9 Monitoring
- **Uptime:** an external checker such as UptimeRobot or Better Stack free tiers **(verify)**, pinging `https://YOUR_DOMAIN`.
- **Resources:** DigitalOcean Monitoring alerts for CPU, memory and disk.
- **Logs:** `docker compose logs`, `journalctl`, `sudo fail2ban-client status sshd`. Bound Docker log size:
  ```bash
  echo '{ "log-driver": "local", "log-opts": { "max-size": "10m", "max-file": "5" } }' | sudo tee /etc/docker/daemon.json
  sudo systemctl restart docker
  ```
- **Updates:** unattended-upgrades for the OS, Dependabot for Python packages, and `docker compose pull` monthly for base images.
- Keep personal data out of logs. Log user IDs, never health values.

---

## 7. Security lab exercises (laptop, staging only)

> ⚖️ **Only attack systems you own.** Point tools at the laptop's staging app, never at production without a deliberate plan and a backup, and never at anything else. Unauthorised scanning and intrusion attempts are crimes in Finland (Rikoslaki 38 luku).

### 7.1 nmap: map your own attack surface
```bash
# Mac: brew install nmap   |  laptop: sudo apt install -y nmap
nmap -sV LAPTOP_IP          # expect only 22 and 5000
nmap -p- LAPTOP_IP          # all ports; is 5433 (Postgres) open? It is until F1 is fixed
```
Exercise: scan before and after removing the DB `ports:` line, and explain the difference.

### 7.2 OWASP ZAP: web app scanning
```bash
docker run --rm -v "$PWD:/zap/wrk:rw" -t ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://LAPTOP_IP:5000 -r zap-report.html
```
The baseline scan is passive and safe. `zap-full-scan.py` actively attacks, so run it on staging only. **Verify** the image name on zaproxy.org.

Exercise: find missing security headers, cookie flags and CSRF issues, fix them, then rescan and compare.

### 7.3 sqlmap: prove the parameterised queries hold
```bash
sudo apt install -y sqlmap
sqlmap -u "http://LAPTOP_IP:5000/ROUTE?param=1" --batch --level 2
sqlmap -u "http://LAPTOP_IP:5000/login" --data "username=a&password=b" --batch   # form fields: check names in the HTML
```
The expected result is "not injectable". Exercise: in a throwaway branch, write one deliberately vulnerable f-string query, watch sqlmap exploit it, then delete the branch.

### 7.4 Manual OWASP Top 10 tests
- **Broken access control:** with users A and B, can A see or change B's results by editing an ID in a URL or form?
- **XSS:** enter `<script>alert(1)</script>` in every text field.
- **CSRF:** can logout or account deletion be triggered from another site's form?
- **Sessions:** in browser devtools, check whether the cookies have `HttpOnly`, `Secure` and `SameSite`, and whether you can read data inside the session cookie (`itsdangerous` cookies are signed, not encrypted).
- **Brute force:** is `/login` rate-limited?

Log each finding in `docs/SECURITY_ROADMAP.md` together with the course concept it teaches.

### 7.5 Hardening audits
```bash
sudo apt install -y lynis && sudo lynis audit system      # raise the "hardening index" over time
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image kunto-laskuri-web
# find the exact image name with: docker images   (verify)
```

---

## 8. Checklist

**Laptop (workshop)**
- [ ] System updated, unattended-upgrades enabled
- [ ] ufw on: SSH + 5000 from LAN only
- [ ] SSH keys only, root login off, fail2ban running
- [ ] Lid and sleep handling disabled, tmux installed
- [ ] Docker installed, only your user in the `docker` group
- [ ] Staging runs from `.env` (chmod 600, git-ignored), no DB port published, no dev mode
- [ ] Only fake data in staging
- [ ] Ollama listening on 127.0.0.1 only, both models pulled
- [ ] `~/bin/review.sh` works

**CI / GitHub**
- [ ] `ci.yml`: pytest, bandit, pip-audit green on GitHub-hosted runners
- [ ] Self-hosted runner as a dedicated non-sudo, non-docker user, running as a service
- [ ] Self-hosted job limited to same-repo PRs; fork PR approval required (or repo private)
- [ ] Dependabot, CodeQL and secret scanning enabled
- [ ] `production` environment with required reviewer and secrets

**Production**
- [ ] Droplet in an EU region, SSH keys only, hardened as in §2, cloud firewall on
- [ ] New strong DB password and `SECRET_KEY` (the old ones are in git history)
- [ ] gunicorn, no debug, web not publicly exposed except through the proxy or tunnel
- [ ] HTTPS via Caddy or Cloudflare Tunnel, security headers set
- [ ] Domain DNS correct, renewal date and price noted (verify)
- [ ] Restricted deploy key with forced command; deploys only after CI passes on `main`
- [ ] Nightly encrypted backups copied off-site; restore tested
- [ ] Uptime and resource alerts; logs bounded; no health data in logs
- [ ] GDPR: privacy notice, data export/delete, provider DPA checked (verify)

**Security lab**
- [ ] nmap shows only expected ports
- [ ] ZAP baseline findings fixed
- [ ] sqlmap: not injectable
- [ ] Access control, XSS, CSRF and session tests done and logged
- [ ] Lynis and Trivy run, top findings fixed
