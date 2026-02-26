"""HTTP client for the EPI backend REST API.

All methods authenticate via Bearer token (API key) and return
parsed JSON responses or raise on HTTP errors.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class EPIBackendClient:
    """Thin wrapper around the EPI backend HTTP API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an authenticated GET request and return parsed JSON."""
        url = f"{self._base_url}{path}"
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
        logger.debug("GET %s params=%s", url, filtered_params)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._headers(), params=filtered_params)
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Endpoint wrappers
    # ------------------------------------------------------------------

    async def get_leads_stats(
        self,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict[str, Any]:
        """GET /api/leads/stats — lead quality breakdown.

        Parameters
        ----------
        site_id : optional UUID string to filter by site.
        date_from : optional ISO-8601 datetime string (inclusive).
        date_to : optional ISO-8601 datetime string (inclusive).
        """
        return await self._get(
            "/api/leads/stats",
            {"site_id": site_id, "date_from": date_from, "date_to": date_to},
        )

    async def get_comparison(
        self,
        site_id: Optional[str] = None,
        platform: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """GET /api/comparison — platform vs EPI attribution comparison.

        Parameters
        ----------
        site_id : optional UUID string to filter by site.
        platform : optional platform name, e.g. ``"google_ads"`` or ``"meta_ads"``.
        date_from : optional ISO-8601 date string (inclusive).
        date_to : optional ISO-8601 date string (inclusive).
        """
        return await self._get(
            "/api/comparison",
            {
                "site_id": site_id,
                "platform": platform,
                "date_from": date_from,
                "date_to": date_to,
            },
        )

    async def get_sites(self) -> list[dict[str, Any]]:
        """GET /api/sites — list all sites for the authenticated agency."""
        return await self._get("/api/sites")

    async def get_me(self) -> dict[str, Any]:
        """GET /api/auth/me — current user / agency info."""
        return await self._get("/api/auth/me")
