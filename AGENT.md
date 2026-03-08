# EPI — Agent Instructions

> **Something broken?** Read [`DEBUGGING.md`](./DEBUGGING.md) — it has quick health checks, log commands, pixel debug mode, common failure modes, and post-deploy verification steps.

## What This Is
Self-serve lead verification and attribution platform. Users sign up (Clerk), add their site, install a pixel, and see scored leads in a dashboard. Free tier: 100 leads. Paid tier: Stripe subscription.

## Architecture

```
Client Website (pixel)
  └─ epi.min.js (auto-detects forms, captures submissions)
       └─ POST /api/event → Cloud Run backend (FastAPI)
              ├─ Pageview → stored in Neon Postgres
              ├─ Form submit → lead pipeline:
              │     dedup → email validation (AbstractAPI Email Reputation)
              │     → phone validation (AbstractAPI Phone Intelligence)
              │     → IP check (AbstractAPI IP Intelligence — VPN/proxy/datacenter)
              │     → bot detection (honeypot + fill time + UA + IP signals)
              │     → attribution (UTM/gclid/fbclid) → quality scoring (0-100)
              │     → save lead → email notification (Resend)
              │     → usage check (free tier: 100 leads, paid: unlimited)
              │     → increment usage_count on user
              └─ Slack bot (separate Cloud Run service, Socket Mode)
                    └─ Claude tool-use agent queries backend API
```

## Infrastructure

| Component | Platform | URL/Location |
|-----------|----------|-------------|
| Backend API | GCP Cloud Run (`epi-platform` project) | `https://epi-backend-146283845133.us-central1.run.app` |
| Frontend | Vercel (`lucs-projects-ee9262c2/frontend`) | `https://frontend-sand-ten-88.vercel.app` |
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
| `backend/app/services/email_validator.py` | AbstractAPI Email Reputation → legacy URL → regex fallback |
| `backend/app/services/phone_validator.py` | AbstractAPI Phone Intelligence → legacy URL → regex fallback |
| `backend/app/services/ip_validator.py` | AbstractAPI IP Intelligence — VPN/proxy/tor/datacenter detection |
| `backend/app/security.py` | Fernet PII encryption, JWT auth, API key auth |
| `backend/app/models/invite_code.py` | Invite code model — SHA-256 hashed codes for self-serve registration |
| `backend/app/routers/auth.py` | Register (with invite code validation), login, API key, /me |
| `backend/app/routers/event.py` | POST /api/event — pixel ingestion, background processing |
| `backend/app/routers/leads.py` | GET /api/leads, /api/leads/recent (decrypted PII), /api/leads/stats |
| `backend/Dockerfile` | Uses `${PORT:-8000}` for Cloud Run compatibility |
| `scripts/generate_invite.py` | CLI to generate invite codes against production DB |
| `frontend/src/lib/require-auth.tsx` | Auth guard — redirects unauthenticated users to login |
| `frontend/src/app/onboarding/install-pixel/page.tsx` | Shows pixel snippet from backend, copy button |
| `slack_bot/app/main.py` | Socket Mode + health server for Cloud Run |
| `slack_bot/app/claude_client.py` | Claude tool-use agent (4 tools: leads stats, recent leads w/ PII, comparison, sites) |
| `pixel/src/index.ts` | Pixel entry point, auto-init on script load |
| `pixel/src/forms.ts` | Form detection + submit interception |

## Deployment

### Backend
```bash
cd backend
docker build --platform=linux/amd64 -t us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest .
docker push us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest
gcloud run deploy epi-backend --image=us-central1-docker.pkg.dev/epi-platform/cloud-run-source-deploy/epi-backend:latest --region=us-central1 --allow-unauthenticated --no-cpu-throttling
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

### Frontend
```bash
cd frontend
npx vercel --prod
```
Env var `NEXT_PUBLIC_API_URL` is set in `.env.production` and on Vercel.

### Migrations
```bash
cd backend
PYTHONPATH=. DATABASE_URL_SYNC="postgresql://neondb_owner:<pass>@ep-patient-flower-aehip8bt.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require" alembic upgrade head
```

### Generate Invite Code
```bash
cd /path/to/repo
PYTHONPATH=backend DATABASE_URL_SYNC="postgresql://neondb_owner:<pass>@ep-patient-flower-aehip8bt.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require" API_KEY_SALT="<production-salt>" python3 scripts/generate_invite.py --label "Client Name - Month Year"
```
Prints a one-time code like `epi-invite-...`. Give to client. Code is SHA-256 hashed in DB (same salt pattern as API keys).

## Env Vars (Backend)
All set on Cloud Run. Secrets in 1Password (`Anthropic API Key`). Key vars:
- `DATABASE_URL` — asyncpg connection string to Neon (use `ssl=require` NOT `sslmode=require` for asyncpg)
- `FERNET_KEY` — 44-char base64 key for PII encryption. MUST be consistent across deploys or encrypted data is lost.
- `RESEND_API_KEY` — Resend email API key
- `NOTIFICATION_EMAIL` — where lead emails go
- `EMAIL_VALIDATION_URL` / `PHONE_VALIDATION_URL` — empty string = use built-in regex fallback
- `ALLOWED_ORIGINS` — comma-separated CORS origins (default `*`). Set to Vercel domain in production if locking down.
- `API_KEY_SALT` — used for hashing API keys AND invite codes. Must match between backend and generate_invite.py.
- `GOOGLE_ADS_DEVELOPER_TOKEN` — Google Ads API developer token
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` — MCC (manager) customer ID if using manager account
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth app credentials
- `META_CLIENT_ID` / `META_CLIENT_SECRET` — Meta OAuth app credentials

## Env Vars (Slack Bot)
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET` — from Slack app settings
- `ANTHROPIC_API_KEY` — from 1Password
- `BACKEND_URL` — full Cloud Run URL of backend
- `EPI_API_KEY` — backend API key for single-tenant mode

## Registered Sites
| Site | Pixel ID | Domain | Verified | Notes |
|------|----------|--------|----------|-------|
| Luc Flynn | `px_JgEFl7EBp0QpXcQn` | lucflynn.com | Yes | Test site, 5 test leads |
| RCU | `px_f_FdtD80OqAAsmGE` | rochesterchristianuniversity.ubpages.com | Yes | 53 leads |
| Chowan University | `px_R35HF4GyB74nYHgx` | start.chowan.edu | Yes | Pixel installed via GTM (`GTM-WBLFFTL3`). Instapage-hosted. |
| SM | `px_1goEwIGl9KauCRiX` | signalmesh.io | No | Test entry |

### GTM Pixel Installation
GTM strips `data-*` attributes from `<script>` tags in Custom HTML. Use this pattern instead:
```html
<script>
(function(){
  var s = document.createElement('script');
  s.src = 'https://epi-backend-146283845133.us-central1.run.app/pixel/epi.min.js';
  s.setAttribute('data-pixel-id', 'PIXEL_ID_HERE');
  s.async = true;
  document.head.appendChild(s);
})();
</script>
```

## Agency Credentials
- Email: `luc@lucflynn.com`
- API Key: `epi_DjEzZdYfOeewQF0e763ibkrs9rCHuXRAX4p4eR9EhtA`

## Auth & Billing

### Auth: Clerk
- **Sign up / Sign in**: Clerk hosted components at `/sign-in` and `/sign-up`. Email/password + Google OAuth.
- **Backend auth**: `security.py` verifies Clerk JWTs via JWKS endpoint. Falls back to legacy JWT and API key auth.
- **Just-in-time user creation**: On first API call with a valid Clerk token, if no user exists, creates User + Agency automatically.
- **Clerk webhook**: `POST /api/clerk/webhook` handles `user.created` events (backup for JIT creation).
- **Env vars**: `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_WEBHOOK_SECRET`

### Billing: Stripe
- **Free tier**: 100 leads scored. No time limit. Leads that arrive after limit are logged but NOT scored (`quality_label = "paused"`).
- **Paid tier**: Stripe Checkout subscription. Usage limit set to 999999 (effectively unlimited).
- **Routes**: `POST /api/billing/create-checkout`, `GET /api/billing/portal`, `POST /api/billing/webhook`
- **Webhook events**: `checkout.session.completed` (upgrade), `invoice.payment_failed` (past_due), `customer.subscription.deleted` (downgrade)
- **Env vars**: `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`

### User model additions
- `clerk_user_id`, `plan` (free/paid/past_due), `usage_count`, `usage_limit`, `stripe_customer_id`, `stripe_subscription_id`
- `hashed_password` is now nullable (Clerk handles passwords)

## Self-Serve Onboarding Flow
Open registration via Clerk. Flow: Sign Up → Dashboard (empty, "Set up your first site" CTA) → Add Site → Pixel snippet with live verification.

- **Pixel snippet**: Backend generates the correct `<script>` tag via `_pixel_snippet()` in `routers/sites.py`, using `settings.backend_url`. Frontend reads it from `GET /api/sites` response.
- **Pixel verification**: Dashboard polls `GET /api/sites` every 5s when any site is pending. Backend sets `pixel_verified=true` on first event.

## Frontend Dashboard
Single-page dashboard with 3 tabs: Leads (feed), Setup (sites + snippets), Usage (plan + billing).
- Uses `@clerk/nextjs` for auth. Middleware protects all routes except `/sign-in` and `/sign-up`.
- API calls use Clerk session tokens via `useAuth().getToken()`.
- Usage warning banner shown at 90%+ of free limit.

## Known Issues / TODOs
- `asyncpg` does not support `sslmode=` param — use `ssl=require` in DATABASE_URL
- Slack bot Claude client uses hardcoded date logic that sometimes picks wrong year
- `/api/leads/stats` with date params can 500 — needs investigation
- Background tasks on Cloud Run require `--no-cpu-throttling` to run after response — now included in deploy command above
- Email/phone/IP validation is LIVE via AbstractAPI (Email Reputation, Phone Intelligence, IP Intelligence). Keys set as env vars on Cloud Run. Falls back to regex if API fails. All API calls have tenacity retry (3 attempts, exponential backoff).
- Google/Meta ad data sync is implemented (`pull_google.py`, `pull_meta.py`) using real APIs. Runs every 6h via APScheduler (3am/9am/3pm/9pm UTC). Requires OAuth tokens on the Agency model + ad account IDs on Sites. First run backfills 7 days. Attribution via URL params (UTM/gclid/fbclid) still works independently.
- Frontend is deployed on Vercel at `https://frontend-sand-ten-88.vercel.app`. Consider adding a custom domain.
- Deploys are manual: docker build + push + gcloud run deploy. See Deployment section above. Frontend: `npx vercel --prod`.
- ~~Fernet key footgun~~ FIXED: security.py now crashes on startup if FERNET_KEY is missing or wrong length
- `ALLOWED_ORIGINS` is set to `*` — tighten to specific Vercel domain when ready
- `backend_url` config (used for pixel snippet generation) defaults to `http://backend:8000` — set `BACKEND_URL` env var on Cloud Run to the actual Cloud Run URL so pixel snippets point to the right host
