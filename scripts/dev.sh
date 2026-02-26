#!/usr/bin/env bash
set -euo pipefail

# EPI Local Development — runs everything without Docker using SQLite
# Usage: bash scripts/dev.sh

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} EPI — Local Development Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Create .env from example if missing
if [ ! -f .env ]; then
    cp .env.example .env
    # Override for local dev (SQLite, localhost URLs)
    cat >> .env <<'LOCALENV'

# --- Local dev overrides ---
DATABASE_URL=sqlite+aiosqlite:///./epi_dev.db
DATABASE_URL_SYNC=sqlite:///./epi_dev.db
BACKEND_URL=http://localhost:8000
MOCK_SERVER_URL=http://localhost:8001
EMAIL_VALIDATION_URL=http://localhost:8001/validate/email
PHONE_VALIDATION_URL=http://localhost:8001/validate/phone
GOOGLE_ADS_API_URL=http://localhost:8001/google-ads
META_ADS_API_URL=http://localhost:8001/meta-ads
LOCALENV
    echo -e "${GREEN}✓ Created .env with local dev overrides${NC}"
fi

# 2. Install backend deps
echo -e "${YELLOW}▸ Installing backend dependencies...${NC}"
cd "$ROOT/backend"
python3 -m pip install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}✓ Backend deps installed${NC}"

# 3. Install mock server deps
echo -e "${YELLOW}▸ Installing mock server dependencies...${NC}"
cd "$ROOT/mocks"
python3 -m pip install -q fastapi uvicorn 2>/dev/null
echo -e "${GREEN}✓ Mock server deps installed${NC}"

# 4. Install frontend deps
echo -e "${YELLOW}▸ Installing frontend dependencies...${NC}"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
    npm install --silent 2>/dev/null || npm install 2>&1 | tail -3
fi
echo -e "${GREEN}✓ Frontend deps installed${NC}"

# 5. Build pixel if not built
cd "$ROOT/pixel"
if [ ! -f dist/epi.min.js ]; then
    echo -e "${YELLOW}▸ Building pixel...${NC}"
    npm install --silent 2>/dev/null || true
    npm run build 2>/dev/null
    echo -e "${GREEN}✓ Pixel built ($(wc -c < dist/epi.min.js | tr -d ' ')B raw, $(wc -c < dist/epi.min.js.gz | tr -d ' ')B gzipped)${NC}"
fi

# Copy pixel to backend static dir
mkdir -p "$ROOT/backend/pixel_dist"
cp "$ROOT/pixel/dist/epi.min.js" "$ROOT/backend/pixel_dist/"
echo -e "${GREEN}✓ Pixel copied to backend/pixel_dist/${NC}"

# 6. Initialize SQLite DB
cd "$ROOT/backend"
echo -e "${YELLOW}▸ Initializing database...${NC}"
DATABASE_URL=sqlite+aiosqlite:///./epi_dev.db \
DATABASE_URL_SYNC=sqlite:///./epi_dev.db \
python3 -c "
from app.database import Base, _create_engine
from app.models import *
from sqlalchemy import create_engine
engine = create_engine('sqlite:///./epi_dev.db')
Base.metadata.create_all(engine)
print('Tables created.')
engine.dispose()
"
echo -e "${GREEN}✓ Database initialized${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} Ready! Start services in 3 terminals:${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "  ${GREEN}Terminal 1 — Mock Server:${NC}"
echo -e "    cd mocks && uvicorn mock_server:app --port 8001 --reload"
echo ""
echo -e "  ${GREEN}Terminal 2 — Backend API:${NC}"
echo -e "    cd backend && DATABASE_URL=sqlite+aiosqlite:///./epi_dev.db DATABASE_URL_SYNC=sqlite:///./epi_dev.db uvicorn app.main:app --port 8000 --reload"
echo ""
echo -e "  ${GREEN}Terminal 3 — Frontend:${NC}"
echo -e "    cd frontend && npm run dev"
echo ""
echo -e "${YELLOW}Then open:${NC}"
echo -e "  Frontend:  http://localhost:3000"
echo -e "  API docs:  http://localhost:8000/docs"
echo -e "  Mock svr:  http://localhost:8001/docs"
echo ""
echo -e "${YELLOW}Quick test flow:${NC}"
echo -e "  1. Register at http://localhost:3000/auth/register"
echo -e "  2. Add a site in the onboarding wizard"
echo -e "  3. Copy the pixel snippet"
echo -e "  4. Test the API: curl http://localhost:8000/api/health"
echo ""
