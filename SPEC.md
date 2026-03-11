# SPEC — Lead Pagination + Google Ads Data Display

## Date
March 10, 2026

## Branch
`feature/leads-pagination-and-google-ads`

## Summary
1. Fix lead pagination — load 25 at a time with "Load more" button and total count
2. Show attribution data on each lead card (Google Ads, UTM, or Direct)
3. Add Google Ads campaign performance tab with summary cards and campaign table

## Files Created
- `backend/app/routers/campaigns.py` — campaign performance endpoint
- `backend/app/schemas/campaign.py` — campaign performance response schema
- `backend/app/routers/google_oauth.py` — Google Ads OAuth connect/disconnect/list
- `backend/app/routers/meta_oauth.py` — Meta Ads OAuth connect/disconnect/list
- `backend/app/routers/slack_oauth.py` — Slack OAuth install/disconnect/list
- `backend/app/models/google_ads_connection.py` — Google Ads connection model
- `backend/app/models/meta_ads_connection.py` — Meta Ads connection model
- `backend/app/models/slack_connection.py` — Slack connection model
- `backend/alembic/versions/005_google_ads_connections.py` — migration
- `backend/alembic/versions/006_meta_ads_connections.py` — migration
- `backend/alembic/versions/007_slack_connections.py` — migration
- `backend/app/models/oauth_state.py` — OAuth state nonce model (CSRF protection)
- `backend/alembic/versions/008_oauth_state_nonces.py` — migration
- `SPEC.md` — this file

## Files Modified
- `backend/app/routers/leads.py` — paginated response with total count, default per_page=25
- `backend/app/routers/campaigns.py` — campaign performance with deduped EPI counts per ad group
- `backend/app/routers/sites.py` — PATCH endpoint for updating google_ads_customer_id
- `backend/app/routers/google_oauth.py` — random state nonce instead of predictable user ID
- `backend/app/routers/meta_oauth.py` — random state nonce instead of predictable user ID
- `backend/app/schemas/lead.py` — added PaginatedLeadResponse schema
- `backend/app/schemas/site.py` — added SiteUpdate schema
- `backend/app/main.py` — registered campaigns, google_oauth, meta_oauth, slack_oauth routers
- `backend/app/models/__init__.py` — import connection models
- `backend/tests/test_leads.py` — updated for paginated response format
- `frontend/src/app/dashboard/page.tsx` — pagination, attribution display, Google Ads tab, restored OAuth panels
- `frontend/src/lib/api.ts` — pagination params, PaginatedLeads type, getCampaignPerformance, updateSite methods

## Files NOT Modified
- `frontend/src/middleware.ts`
- `backend/app/security.py`
- `backend/app/config.py`
- `pixel/` (any file)
- `slack_bot/` (any file)
- `Dockerfile` or `docker-compose.yml`
- `scripts/deploy_backend.sh`
- `requirements.txt`
- `package.json`
