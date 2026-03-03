import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, health, event, leads, sites, comparison, jobs
from app.middleware.rate_limit import RateLimitMiddleware
from app.jobs.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Suppress PII in logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="EPI — Electro-PI",
    description="First-party lead verification and attribution platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
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
