import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, health, event, leads, sites, comparison, jobs, stripe_billing, clerk_webhook, google_oauth, meta_oauth, slack_oauth, campaigns
from app.middleware.rate_limit import RateLimitMiddleware
from app.jobs.scheduler import start_scheduler


# ── Structured JSON logging ──
class JSONFormatter(logging.Formatter):
    """Outputs one JSON object per line — Cloud Run parses these natively."""

    def format(self, record):
        log = {
            "timestamp": self.formatTime(record),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(logging.INFO)

# Suppress PII in logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# ── Sentry error tracking ──
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production" if settings.is_production else "development",
    )
    logging.getLogger(__name__).info("Sentry initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if production secrets are still dev defaults
    settings.validate_production_config()
    start_scheduler()
    yield


app = FastAPI(
    title="EPI — Electro-PI",
    description="First-party lead verification and attribution platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — pixel/event endpoints need open access (any website embeds the pixel),
# but authenticated endpoints should restrict to known origins.
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
if _origins == ["*"]:
    # Open CORS — acceptable in early stage when pixel can be on any domain.
    # Tighten to specific Vercel domain + client domains when ready.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # credentials=True + origins=* is invalid anyway
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(event.router)
app.include_router(leads.router)
app.include_router(sites.router)
app.include_router(comparison.router)
app.include_router(jobs.router)
app.include_router(stripe_billing.router)
app.include_router(clerk_webhook.router)
app.include_router(google_oauth.router)
app.include_router(meta_oauth.router)
app.include_router(slack_oauth.router)
app.include_router(campaigns.router)

# Serve pixel JS as static file
import pathlib
_pixel_dirs = [
    pathlib.Path(__file__).resolve().parent.parent / "pixel_dist",  # local dev
    pathlib.Path("/app/pixel_dist"),  # Docker
]
for _pd in _pixel_dirs:
    if _pd.is_dir():
        app.mount("/pixel", StaticFiles(directory=str(_pd)), name="pixel")
        break
