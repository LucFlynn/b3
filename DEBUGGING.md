# EPI — Debugging Guide

Reference for diagnosing production issues. Read this when something is broken.

## Quick Health Checks

Run these first to narrow down where the problem is:

```bash
BACKEND="https://epi-backend-146283845133.us-central1.run.app"

# 1. Is the backend up?
curl -s "$BACKEND/api/health" | python3 -m json.tool

# 2. Is the event endpoint accepting events? (both content types)
curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND/api/event" \
  -H "Content-Type: text/plain" \
  -d '{"pixel_id":"px_JgEFl7EBp0QpXcQn","event_type":"pageview","visitor_id":"debug-test","session_id":"debug-test","page_url":"https://debug-test"}'

curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND/api/event" \
  -H "Content-Type: application/json" \
  -d '{"pixel_id":"px_JgEFl7EBp0QpXcQn","event_type":"pageview","visitor_id":"debug-test","session_id":"debug-test","page_url":"https://debug-test"}'

# Both should return 202. If text/plain returns 422, the sendBeacon parsing is broken.

# 3. Is the pixel JS being served?
curl -s -o /dev/null -w "%{http_code}" "$BACKEND/pixel/epi.min.js"
# Should return 200.

# 4. Can the backend reach the database?
# Check the "db" field in the /api/health response above. "connected" = good, "unreachable" = bad.
```

## Cloud Run Logs

```bash
# Recent errors (last hour)
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="epi-backend" AND severity>=ERROR' \
  --project=epi-platform --limit=30 --freshness=1h \
  --format='table(timestamp,jsonPayload.message,textPayload)'

# All event endpoint traffic (last hour)
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="epi-backend" AND (textPayload=~"/api/event" OR jsonPayload.message=~"/api/event")' \
  --project=epi-platform --limit=50 --freshness=1h \
  --format='table(timestamp,textPayload)'

# Dead-letter events (processing failed after 3 retries)
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="epi-backend" AND (textPayload=~"DEAD_LETTER" OR jsonPayload.message=~"DEAD_LETTER")' \
  --project=epi-platform --limit=20 --freshness=24h \
  --format='table(timestamp,jsonPayload.message,textPayload)'

# Slack bot logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="epi-slackbot"' \
  --project=epi-platform --limit=30 --freshness=1h \
  --format='table(timestamp,jsonPayload.message,textPayload)'
```

## Pixel Debug Mode

The pixel has a built-in debug mode that logs all events and response codes to the browser console.

**Activate it** by either:
- Adding `data-debug` to the script tag: `<script src="..." data-pixel-id="px_..." data-debug></script>`
- Appending `?epi_debug=1` to any page URL that has the pixel installed

When active, the console will show:
```
[EPI debug] pixel_id: px_abc123 endpoint: https://epi-backend-146283845133.us-central1.run.app/api/event
[EPI debug] sending: pageview {pixel_id: "px_abc123", ...}
[EPI debug] pageview -> 202 OK
[EPI debug] sending: form_submit {pixel_id: "px_abc123", form_data: {...}, ...}
[EPI debug] form_submit -> 202 OK
```

If you see errors like `-> 422` or `network error`, the problem is between the pixel and the backend.

**Important**: Debug mode uses `fetch` instead of `sendBeacon` so it can read the response. This means it sends `application/json` instead of `text/plain`. If you suspect a content-type parsing issue specifically, test with curl (see Quick Health Checks above).

## Common Failure Modes

### Events returning 422 Unprocessable Entity
**Symptom**: Pageviews stop flowing, no new leads, pixel status shows stale data.
**Cause**: The event endpoint can't parse the request body. Most likely a content-type issue — `sendBeacon` sends `text/plain` and the backend must parse JSON from raw body.
**Check**: `curl -X POST ... -H "Content-Type: text/plain"` (see Quick Health Checks).
**Fix location**: `backend/app/routers/event.py` — the `ingest_event()` handler manually parses `request.body()` as JSON. If someone changes this back to a Pydantic body parameter (`event: EventPayload`), text/plain will break.

### Pageview count stuck / showing 0
**Symptom**: Dashboard pixel status bar shows 0 or 1 pageviews.
**Possible causes**:
1. Events are 422ing (see above) — check logs for HTTP status codes
2. Timezone: `pixel-status` endpoint counts pageviews where `created_at >= today 00:00 UTC`. If you're checking late at night US time, "today" in UTC might be tomorrow. Not a bug, just UTC.
3. Backend was down — check Cloud Run revision history: `gcloud run revisions list --service=epi-backend --region=us-central1 --project=epi-platform`

### Form submissions not appearing as leads
**Symptom**: Pageviews work but no leads show up.
**Check in order**:
1. Is the pixel detecting form submissions? Use debug mode (see above) — you should see `form_submit` events in console.
2. Are form_submit events reaching the backend? Check logs for `POST /api/event` with 202 status.
3. Is the lead pipeline succeeding? Check for dead-letter logs (see Cloud Run Logs above).
4. Is the user over their usage limit? Leads beyond the limit are stored with `quality_label = "paused"` and won't appear in the normal leads feed.

### CORS errors
**Symptom**: Browser console shows "blocked by CORS policy" on event requests.
**Context**: `sendBeacon` with `text/plain` avoids CORS preflight entirely — this is by design. If you see CORS errors, it means either:
1. The pixel fell back to `fetch` (sendBeacon unavailable or failed) which sends `application/json` and triggers preflight
2. Someone changed the pixel to use a content type that triggers preflight
**Fix**: `ALLOWED_ORIGINS` env var on Cloud Run (currently `*`). Or ensure the pixel uses `text/plain` for sendBeacon.

### Backend won't start / crashes on boot
**Symptom**: Cloud Run revision fails health check.
**Check**: `gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="epi-backend" AND severity>=ERROR' --project=epi-platform --limit=10 --freshness=30m`
**Common causes**:
- `FERNET_KEY` missing or wrong length — `security.py` crashes on startup intentionally
- `DATABASE_URL` using `sslmode=require` instead of `ssl=require` — asyncpg rejects it
- Dev-default secrets in production — `config.py` `validate_production_config()` raises `RuntimeError`

### Database connection failures
**Symptom**: `/api/health` returns `"db": "unreachable"`, or 500 errors on API calls.
**Check**: Neon dashboard at https://console.neon.tech — look for connection limits, maintenance, or suspended project.
**Note**: Neon free tier suspends after 5 min of inactivity. First request after suspension has a cold-start delay (~1-3s). This can cause intermittent timeouts but should self-resolve.

## Monitoring & Alerts

Cloud Monitoring alert policies are set up on `epi-platform`:
- **EPI: Event Ingestion 4xx Rate > 10%** — fires if >10% of requests return 4xx over 5 min
- **EPI: Backend 5xx Rate > 5%** — fires if >5% of requests return 5xx over 5 min
- Alerts email `luc@lucflynn.com`
- Setup script: `scripts/setup_monitoring.sh` (idempotent, safe to re-run)

## Post-Deploy Verification

Always run after deploying the backend. The deploy script (`scripts/deploy_backend.sh`) does this automatically in Step 6, but you can run it manually:

```bash
BACKEND="https://epi-backend-146283845133.us-central1.run.app"
PAYLOAD='{"pixel_id":"px_JgEFl7EBp0QpXcQn","event_type":"pageview","visitor_id":"smoke-test","session_id":"smoke-test","page_url":"https://smoke-test"}'

# Must be 202
curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND/api/event" -H "Content-Type: text/plain" -d "$PAYLOAD"

# Must be 202
curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND/api/event" -H "Content-Type: application/json" -d "$PAYLOAD"

# Must be 422 (not 500)
curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND/api/event" -H "Content-Type: text/plain" -d "not json"
```

If any of these fail, the deploy broke event ingestion. **Do not walk away until all three pass.**

## Lessons Learned

| Date | Issue | Root Cause | How We'd Catch It Now |
|------|-------|------------|----------------------|
| 2026-03-07 | All pixel events returning 422 for days | sendBeacon sends `text/plain`, FastAPI only parses `application/json` body params. Fixed by manually parsing `request.body()` as JSON. | Post-deploy smoke test (text/plain curl), 4xx monitoring alert |
