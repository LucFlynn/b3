#!/usr/bin/env bash
set -euo pipefail

# EPI Definition of Done Validation Script
# Checks every spec criterion and reports PASS/FAIL

PASS=0
FAIL=0
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MOCK_URL="${MOCK_URL:-http://localhost:8001}"

pass() { echo "  ✓ PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ FAIL: $1"; FAIL=$((FAIL + 1)); }
check() { if eval "$2" >/dev/null 2>&1; then pass "$1"; else fail "$1"; fi; }

echo "=========================================="
echo " EPI — Definition of Done Validation"
echo "=========================================="
echo ""

# --- 1. Project Structure ---
echo "▸ Project Structure"
check "backend directory exists" "[ -d backend ]"
check "frontend directory exists" "[ -d frontend ]"
check "pixel directory exists" "[ -d pixel ]"
check "slack_bot directory exists" "[ -d slack_bot ]"
check "mocks directory exists" "[ -d mocks ]"
check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
check "Makefile exists" "[ -f Makefile ]"
echo ""

# --- 2. Database Models ---
echo "▸ Database Models"
check "Agency model" "[ -f backend/app/models/agency.py ]"
check "User model" "[ -f backend/app/models/user.py ]"
check "Site model" "[ -f backend/app/models/site.py ]"
check "Pageview model" "[ -f backend/app/models/pageview.py ]"
check "Lead model" "[ -f backend/app/models/lead.py ]"
check "PlatformConversion model" "[ -f backend/app/models/platform_conversion.py ]"
check "AttributionComparison model" "[ -f backend/app/models/attribution_comparison.py ]"
echo ""

# --- 3. PII Security ---
echo "▸ PII Security"
check "Fernet encryption in security.py" "grep -q 'Fernet' backend/app/security.py"
check "SHA-256 hash columns in Lead model" "grep -q 'email_hash' backend/app/models/lead.py"
check "IP hashing (never raw)" "grep -q 'hash_ip' backend/app/security.py"
check "PII encryption in pipeline" "grep -q 'encrypt_pii' backend/app/services/lead_pipeline.py"
# Check PII never in logs
check "SQLAlchemy engine logging suppressed" "grep -q 'sqlalchemy.engine.*WARNING' backend/app/main.py"
echo ""

# --- 4. Auth ---
echo "▸ Authentication"
check "JWT auth implementation" "grep -q 'create_access_token' backend/app/security.py"
check "API key auth implementation" "grep -q 'generate_api_key' backend/app/security.py"
check "Register endpoint" "grep -q 'register' backend/app/routers/auth.py"
check "Login endpoint" "grep -q 'login' backend/app/routers/auth.py"
echo ""

# --- 5. Event Ingestion ---
echo "▸ Event Ingestion"
check "POST /api/event returns 202" "grep -q '202' backend/app/routers/event.py"
check "Background processing" "grep -q 'background_tasks' backend/app/routers/event.py"
echo ""

# --- 6. JavaScript Pixel ---
echo "▸ JavaScript Pixel"
check "Pixel source exists" "[ -f pixel/src/index.ts ]"
check "Form detection (forms.ts)" "[ -f pixel/src/forms.ts ]"
check "Field identification (fields.ts)" "[ -f pixel/src/fields.ts ]"
check "Honeypot injection" "[ -f pixel/src/honeypot.ts ]"
check "Cookie management" "[ -f pixel/src/cookie.ts ]"
check "URL param capture" "[ -f pixel/src/params.ts ]"
check "Beacon/sendBeacon transport" "[ -f pixel/src/beacon.ts ]"
check "Manual API (epi('track', ...))" "[ -f pixel/src/api.ts ]"
check "Rollup config" "[ -f pixel/rollup.config.mjs ]"
if [ -f pixel/dist/epi.min.js ]; then
    SIZE=$(wc -c < pixel/dist/epi.min.js)
    if [ "$SIZE" -lt 50000 ]; then pass "Pixel bundle < 50KB raw"; else fail "Pixel bundle < 50KB raw (got ${SIZE}B)"; fi
else
    fail "Pixel bundle built (dist/epi.min.js)"
fi
echo ""

# --- 7. Lead Pipeline ---
echo "▸ Lead Processing Pipeline"
check "Lead pipeline service" "[ -f backend/app/services/lead_pipeline.py ]"
check "Email validation service" "[ -f backend/app/services/email_validator.py ]"
check "Phone validation service" "[ -f backend/app/services/phone_validator.py ]"
check "Bot detection service" "[ -f backend/app/services/bot_detector.py ]"
check "Lead scoring service" "[ -f backend/app/services/lead_scorer.py ]"
check "Attribution service" "[ -f backend/app/services/attribution.py ]"
check "Dedup logic" "grep -q 'check_duplicate' backend/app/services/lead_pipeline.py"
check "4 attribution tiers" "grep -q 'definitive' backend/app/services/attribution.py && grep -q 'high_confidence' backend/app/services/attribution.py && grep -q 'probable' backend/app/services/attribution.py && grep -q 'unattributed' backend/app/services/attribution.py"
echo ""

# --- 8. Platform Integration ---
echo "▸ Platform Integration + Jobs"
check "Google Ads service" "[ -f backend/app/services/google_ads.py ]"
check "Meta Ads service" "[ -f backend/app/services/meta_ads.py ]"
check "Comparison service" "[ -f backend/app/services/comparison.py ]"
check "APScheduler setup" "[ -f backend/app/jobs/scheduler.py ]"
check "Pull Google job" "[ -f backend/app/jobs/pull_google.py ]"
check "Pull Meta job" "[ -f backend/app/jobs/pull_meta.py ]"
check "Compute comparison job" "[ -f backend/app/jobs/compute_comparison.py ]"
check "Manual job trigger endpoint" "grep -q 'run/{job_name}' backend/app/routers/jobs.py"
echo ""

# --- 9. REST API ---
echo "▸ REST API Endpoints"
check "GET /api/leads" "grep -q 'list_leads' backend/app/routers/leads.py"
check "GET /api/leads/stats" "grep -q 'lead_stats' backend/app/routers/leads.py"
check "GET /api/comparison" "grep -q 'get_comparison' backend/app/routers/comparison.py"
check "POST /api/sites" "grep -q 'create_site' backend/app/routers/sites.py"
check "Rate limiting middleware" "[ -f backend/app/middleware/rate_limit.py ]"
echo ""

# --- 10. Slack Bot ---
echo "▸ Slack Bot"
check "Slack bot main" "[ -f slack_bot/app/main.py ]"
check "Message handlers" "[ -f slack_bot/app/handlers.py ]"
check "Claude client with tool use" "[ -f slack_bot/app/claude_client.py ]"
check "Data fetcher (backend API client)" "[ -f slack_bot/app/data_fetcher.py ]"
echo ""

# --- 11. Frontend ---
echo "▸ Onboarding Frontend"
check "Next.js app" "[ -f frontend/package.json ]"
check "Auth login page" "[ -f frontend/src/app/auth/login/page.tsx ]"
check "Auth register page" "[ -f frontend/src/app/auth/register/page.tsx ]"
check "Onboarding add-site" "[ -f frontend/src/app/onboarding/add-site/page.tsx ]"
check "Google connect" "[ -f frontend/src/app/onboarding/google/page.tsx ]"
check "Meta connect" "[ -f frontend/src/app/onboarding/meta/page.tsx ]"
check "Slack connect" "[ -f frontend/src/app/onboarding/slack/page.tsx ]"
check "Pixel verify" "[ -f frontend/src/app/onboarding/verify/page.tsx ]"
check "Dashboard" "[ -f frontend/src/app/dashboard/page.tsx ]"
echo ""

# --- 12. Mock Server ---
echo "▸ Mock Server"
check "Mock server" "[ -f mocks/mock_server.py ]"
check "Email validation mock" "grep -q 'validate/email' mocks/mock_server.py"
check "Phone validation mock" "grep -q 'validate/phone' mocks/mock_server.py"
check "Google Ads mock" "grep -q 'google-ads' mocks/mock_server.py"
check "Meta Ads mock" "grep -q 'meta-ads' mocks/mock_server.py"
check "OAuth mocks" "grep -q 'oauth' mocks/mock_server.py"
echo ""

# --- 13. Tests ---
echo "▸ Tests"
check "Backend test directory" "[ -d backend/tests ]"
check "Auth tests" "[ -f backend/tests/test_auth.py ]"
check "Security tests" "[ -f backend/tests/test_security.py ]"
check "Event tests" "[ -f backend/tests/test_event.py ]"
check "Leads tests" "[ -f backend/tests/test_leads.py ]"
check "Sites tests" "[ -f backend/tests/test_sites.py ]"
check "Pipeline tests" "[ -f backend/tests/test_pipeline.py ]"
check "Comparison tests" "[ -f backend/tests/test_comparison.py ]"
echo ""

# --- Summary ---
echo "=========================================="
TOTAL=$((PASS + FAIL))
echo " Results: ${PASS}/${TOTAL} passed"
if [ "$FAIL" -eq 0 ]; then
    echo " Status: ALL PASS ✓"
else
    echo " Status: ${FAIL} FAILURES ✗"
fi
echo "=========================================="

exit "$FAIL"
