import time
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# Auth endpoints get much stricter limits (brute-force protection)
_AUTH_PATHS = {"/api/auth/login", "/api/auth/register"}
_AUTH_LIMIT_PER_MINUTE = 10


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter with stricter limits on auth endpoints.

    NOTE: In-memory state resets when Cloud Run recycles the instance and
    doesn't share across instances. For true distributed rate limiting,
    swap to Redis/Memorystore. This is still useful as a per-instance guard.
    """

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._auth_requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and pixel
        path = request.url.path
        if path in ("/api/health", "/pixel/epi.min.js"):
            return await call_next(request)

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        now = time.time()

        # Stricter limit on auth endpoints
        if path in _AUTH_PATHS and request.method == "POST":
            window = 60  # 1 minute
            self._auth_requests[client_ip] = [
                t for t in self._auth_requests[client_ip] if now - t < window
            ]
            if len(self._auth_requests[client_ip]) >= _AUTH_LIMIT_PER_MINUTE:
                raise HTTPException(status_code=429, detail="Too many attempts, try again later")
            self._auth_requests[client_ip].append(now)

        # General rate limit
        window = 3600  # 1 hour
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < window
        ]
        if len(self._requests[client_ip]) >= settings.rate_limit_per_hour:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        self._requests[client_ip].append(now)

        return await call_next(request)
