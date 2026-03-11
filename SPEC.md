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
- `SPEC.md` — this file

## Files Modified
- `backend/app/routers/leads.py` — paginated response with total count, default per_page=25
- `backend/app/schemas/lead.py` — added PaginatedLeadResponse schema
- `backend/app/main.py` — registered campaigns router
- `frontend/src/app/dashboard/page.tsx` — pagination, attribution display, Google Ads tab
- `frontend/src/lib/api.ts` — pagination params, PaginatedLeads type, getCampaignPerformance method

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
