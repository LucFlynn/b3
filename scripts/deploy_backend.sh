#!/usr/bin/env bash
set -euo pipefail

# EPI Backend Deploy Script
# Runs migrations then builds + pushes + deploys to Cloud Run.
# Usage: ./scripts/deploy_backend.sh

PROJECT="epi-platform"
REGION="us-central1"
IMAGE="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/epi-backend:latest"
SERVICE="epi-backend"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${REPO_ROOT}/backend"

echo "=== EPI Backend Deploy ==="

# ── Step 1: Run migrations ──
echo ""
echo "→ Running database migrations..."
if [ -z "${DATABASE_URL_SYNC:-}" ]; then
    echo "ERROR: DATABASE_URL_SYNC not set. Export it before deploying:"
    echo '  export DATABASE_URL_SYNC="postgresql://neondb_owner:<pass>@ep-patient-flower-aehip8bt.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"'
    exit 1
fi

cd "$BACKEND_DIR"
PYTHONPATH=. alembic upgrade head
echo "✓ Migrations complete"

# ── Step 2: Build Docker image ──
echo ""
echo "→ Building Docker image..."
docker build --platform=linux/amd64 -t "$IMAGE" .
echo "✓ Image built"

# ── Step 3: Push to Artifact Registry ──
echo ""
echo "→ Pushing to Artifact Registry..."
docker push "$IMAGE"
echo "✓ Image pushed"

# ── Step 4: Deploy to Cloud Run ──
echo ""
echo "→ Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
    --image="$IMAGE" \
    --region="$REGION" \
    --project="$PROJECT" \
    --allow-unauthenticated \
    --no-cpu-throttling
echo "✓ Deployed"

# ── Step 5: Verify ──
echo ""
echo "→ Verifying deployment..."
sleep 5
HEALTH=$(curl -s "https://epi-backend-146283845133.${REGION}.run.app/api/health")
echo "  Health check: $HEALTH"

echo ""
echo "=== Deploy complete ==="
