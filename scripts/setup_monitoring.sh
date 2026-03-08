#!/usr/bin/env bash
set -euo pipefail

# Sets up Cloud Monitoring alert policies for EPI backend.
# Run once: ./scripts/setup_monitoring.sh
# Requires: gcloud CLI authenticated with epi-platform project.

PROJECT="epi-platform"
SERVICE="epi-backend"
NOTIFICATION_EMAIL="luc@lucflynn.com"

echo "=== EPI Monitoring Setup ==="

TOKEN=$(gcloud auth print-access-token 2>/dev/null)
BASE="https://monitoring.googleapis.com/v3/projects/${PROJECT}"

# ── Step 1: Create notification channel (email) ──
echo ""
echo "→ Creating email notification channel..."

# Check if it already exists
EXISTING=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "${BASE}/notificationChannels" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for ch in data.get('notificationChannels', []):
    if ch.get('type') == 'email' and ch.get('labels', {}).get('email_address') == '${NOTIFICATION_EMAIL}':
        print(ch['name'])
        break
" 2>/dev/null || true)

if [ -n "$EXISTING" ]; then
    CHANNEL_ID="$EXISTING"
    echo "  Already exists: $CHANNEL_ID"
else
    CHANNEL_ID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "${BASE}/notificationChannels" \
        -d "{
            \"type\": \"email\",
            \"displayName\": \"EPI Alerts\",
            \"labels\": {\"email_address\": \"${NOTIFICATION_EMAIL}\"}
        }" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])")
    echo "  Created: $CHANNEL_ID"
fi

# ── Step 2: Create alert — event ingestion 4xx spike ──
echo ""
echo "→ Creating alert: Event Ingestion 4xx Spike..."

EXISTING_POLICY=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "${BASE}/alertPolicies" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('alertPolicies', []):
    if 'Event Ingestion 4xx' in p.get('displayName', ''):
        print(p['name'])
        break
" 2>/dev/null || true)

if [ -n "$EXISTING_POLICY" ]; then
    echo "  Already exists: $EXISTING_POLICY"
else
    curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "${BASE}/alertPolicies" \
        -d "{
            \"displayName\": \"EPI: Event Ingestion 4xx Rate > 10%\",
            \"documentation\": {
                \"content\": \"More than 10% of POST /api/event requests returned 4xx in the last 5 minutes. Pixel events are likely being rejected. Check event endpoint for parsing or schema issues.\",
                \"mimeType\": \"text/markdown\"
            },
            \"conditions\": [{
                \"displayName\": \"4xx rate on epi-backend > 10%\",
                \"conditionThreshold\": {
                    \"filter\": \"resource.type = \\\"cloud_run_revision\\\" AND resource.labels.service_name = \\\"${SERVICE}\\\" AND metric.type = \\\"run.googleapis.com/request_count\\\" AND metric.labels.response_code_class = \\\"4xx\\\"\",
                    \"aggregations\": [{
                        \"alignmentPeriod\": \"300s\",
                        \"perSeriesAligner\": \"ALIGN_RATE\"
                    }],
                    \"comparison\": \"COMPARISON_GT\",
                    \"thresholdValue\": 0.1,
                    \"duration\": \"300s\",
                    \"trigger\": {\"count\": 1}
                }
            }],
            \"combiner\": \"OR\",
            \"enabled\": true,
            \"notificationChannels\": [\"${CHANNEL_ID}\"],
            \"alertStrategy\": {\"autoClose\": \"1800s\"}
        }" > /dev/null
    echo "  Created"
fi

# ── Step 3: Create alert — backend 5xx error rate ──
echo ""
echo "→ Creating alert: Backend 5xx Error Rate..."

EXISTING_POLICY=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "${BASE}/alertPolicies" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('alertPolicies', []):
    if '5xx Rate' in p.get('displayName', ''):
        print(p['name'])
        break
" 2>/dev/null || true)

if [ -n "$EXISTING_POLICY" ]; then
    echo "  Already exists: $EXISTING_POLICY"
else
    curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "${BASE}/alertPolicies" \
        -d "{
            \"displayName\": \"EPI: Backend 5xx Rate > 5%\",
            \"documentation\": {
                \"content\": \"More than 5% of requests to epi-backend returned 5xx in the last 5 minutes. Check Cloud Run logs for stack traces.\",
                \"mimeType\": \"text/markdown\"
            },
            \"conditions\": [{
                \"displayName\": \"5xx rate on epi-backend > 5%\",
                \"conditionThreshold\": {
                    \"filter\": \"resource.type = \\\"cloud_run_revision\\\" AND resource.labels.service_name = \\\"${SERVICE}\\\" AND metric.type = \\\"run.googleapis.com/request_count\\\" AND metric.labels.response_code_class = \\\"5xx\\\"\",
                    \"aggregations\": [{
                        \"alignmentPeriod\": \"300s\",
                        \"perSeriesAligner\": \"ALIGN_RATE\"
                    }],
                    \"comparison\": \"COMPARISON_GT\",
                    \"thresholdValue\": 0.05,
                    \"duration\": \"300s\",
                    \"trigger\": {\"count\": 1}
                }
            }],
            \"combiner\": \"OR\",
            \"enabled\": true,
            \"notificationChannels\": [\"${CHANNEL_ID}\"],
            \"alertStrategy\": {\"autoClose\": \"1800s\"}
        }" > /dev/null
    echo "  Created"
fi

echo ""
echo "=== Monitoring setup complete ==="
echo "Alerts will email ${NOTIFICATION_EMAIL} when triggered."
