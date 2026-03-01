# EPI — Agent Instructions

## What This Is
Lead verification and attribution platform. Pixel on client sites captures pageviews and form submissions, processes them through a scoring pipeline, and delivers notifications via email (Resend) and Slack bot (Claude-powered).

## Architecture

```
Client Website (pixel)
  └─ epi.min.js (auto-detects forms, captures submissions)
       └─ POST /api/event → Cloud Run backend (FastAPI)
              ├─ Pageview → stored in Neon Postgres
              ├─ Form submit → lead pipeline:
              │     dedup → email/phone regex validation → bot detection
              │     → attribution (UTM/gclid/fbclid) → quality scoring (0-100)
              │     → save lead → email notification (Resend)
              └─ Slack bot (separate Cloud Run service, Socket Mode)
                    └─ Claude tool-use agent queries backend API
```

## Infrastructure

| Component | Platform | URL/Location |
|-----------|----------|-------------|
| Backend API | GCP Cloud Run (`epi-platform` project) | `https://epi-backend-146283845133.us-central1.run.app` |
| Slack Bot | GCP Cloud Run (`epi-platform` project) | `https://epi-slackbot-146283845133.us-central1.run.app` |
| Database | Neon Postgres (org: `org-young-sunset-49678650`) | `ep-patient-flower-aehip8bt.c-2.us-east-2.aws.neon.tech/neondb` |
| Pixel JS | Served by backend at `/pixel/epi.min.js` | Built from `pixel/` dir via Rollup |
| Email | Resend | `onboarding@resend.dev` → `luc@lucflynn.com` |
| Docker images | GCP Artifact Registry | `us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/` |

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point, mounts routers + pixel static dir |
| `backend/app/config.py` | All env var config (pydantic-settings) |
| `backend/app/services/lead_pipeline.py` | Core pipeline: dedup → validate → score → attribute → notify |
| `backend/app/services/email_notifier.py` | Resend email notification on new leads |
| `backend/app/services/email_validator.py` | Regex fallback when no external validation URL |
| `backend/app/services/phone_validator.py` | Regex fallback when no external validation URL |
| `backend/app/security.py` | Fernet PII encryption, JWT auth, API key auth |
| `backend/app/routers/event.py` | POST /api/event — pixel ingestion, background processing |
| `backend/Dockerfile` | Uses `${PORT:-8000}` for Cloud Run compatibility |
| `slack_bot/app/main.py` | Socket Mode + health server for Cloud Run |
| `slack_bot/app/claude_client.py` | Claude tool-use agent (3 tools: leads stats, comparison, sites) |
| `pixel/src/index.ts` | Pixel entry point, auto-init on script load |
| `pixel/src/forms.ts` | Form detection + submit interception |

## Deployment

### Backend
```bash
cd backend
docker build --platform=linux/amd64 -t us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest .
docker push us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest
gcloud run deploy epi-backend --image=us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest --region=us-central1 --allow-unauthenticated
```

### Slack Bot
```bash
cd slack_bot
docker build --platform=linux/amd64 -t us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-slackbot:latest .
docker push us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-slackbot:latest
gcloud run deploy epi-slackbot --image=us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-slackbot:latest --region=us-central1 --min-instances=1
```

### Pixel
```bash
cd pixel && npm install && npm run build
cp dist/epi.min.js ../backend/pixel_dist/epi.min.js
# Then rebuild + redeploy backend
```

### Migrations
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. DATABASE_URL_SYNC="postgresql://neondb_owner:<pass>@ep-patient-flower-aehip8bt.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```

## Env Vars (Backend)
All set on Cloud Run. Secrets in 1Password (`Anthropic API Key`). Key vars:
- `DATABASE_URL` — asyncpg connection string to Neon (use `ssl=require` NOT `sslmode=require` for asyncpg)
- `FERNET_KEY` — 44-char base64 key for PII encryption. MUST be consistent across deploys or encrypted data is lost.
- `RESEND_API_KEY` — Resend email API key
- `NOTIFICATION_EMAIL` — where lead emails go
- `EMAIL_VALIDATION_URL` / `PHONE_VALIDATION_URL` — empty string = use built-in regex fallback

## Env Vars (Slack Bot)
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET` — from Slack app settings
- `ANTHROPIC_API_KEY` — from 1Password
- `BACKEND_URL` — full Cloud Run URL of backend
- `EPI_API_KEY` — backend API key for single-tenant mode

## Registered Sites
| Site | Pixel ID | Domain |
|------|----------|--------|
| Luc Flynn | `px_JgEFl7EBp0QpXcQn` | lucflynn.com |
| RCU | `px_f_FdtD80OqAAsmGE` | rochesterchristianuniversity.ubpages.com |

## Agency Credentials
- Email: `luc@lucflynn.com`
- API Key: `epi_DjEzZdYfOeewQF0e763ibkrs9rCHuXRAX4p4eR9EhtA`

## Known Issues / TODOs
- `asyncpg` does not support `sslmode=` param — use `ssl=require` in DATABASE_URL
- Slack bot Claude client uses hardcoded date logic that sometimes picks wrong year
- `/api/leads/stats` with date params can 500 — needs investigation
- Background tasks on Cloud Run require `--no-cpu-throttling` to run after response
- No real email/phone validation service — using regex fallback
- No Google/Meta ad data sync — attribution works via URL params only
- Frontend dashboard exists but is not deployed (not needed — Slack bot is the UI)
- Code is not commented — next agent should add docstrings to services and routers
- No CI/CD pipeline — deploys are manual docker build + push + gcloud
- Fernet key footgun in security.py: if key is not exactly 44 chars, a random key is silently generated (breaks all existing encrypted data)
