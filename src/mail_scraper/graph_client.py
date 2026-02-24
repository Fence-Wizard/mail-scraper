import asyncio
import logging
import time
from typing import Any, AsyncGenerator

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class GraphClient:
    def __init__(self, timeout_seconds: int = 30) -> None:
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._graph_endpoint = settings.graph_endpoint.rstrip("/")

    async def __aenter__(self) -> "GraphClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def authenticate(self, force_refresh: bool = False) -> None:
        if not force_refresh and self._token and time.time() < self._token_expires_at:
            return

        url = f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }
        resp = await self._client.post(url, data=data)
        resp.raise_for_status()
        payload = resp.json()

        self._token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        self._token_expires_at = time.time() + max(30, expires_in - 60)

    async def _ensure_token(self) -> None:
        if not self._token or time.time() >= self._token_expires_at:
            await self.authenticate()

    @staticmethod
    def _normalize_graph_path(path_or_url: str) -> str:
        if path_or_url.startswith("https://graph.microsoft.com"):
            parts = path_or_url.split("/v1.0", 1)
            return parts[1] if len(parts) > 1 else "/"
        return path_or_url

    async def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> Any:
        await self._ensure_token()
        path = self._normalize_graph_path(path_or_url)
        url = f"{self._graph_endpoint}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            # Immutable IDs remain stable when items move between folders.
            "Prefer": 'IdType="ImmutableId"',
        }

        for attempt in range(6):
            resp = await self._client.request(method, url, headers=headers, params=params)

            if resp.status_code == 401 and attempt == 0:
                await self.authenticate(force_refresh=True)
                headers["Authorization"] = f"Bearer {self._token}"
                continue

            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After")
                if retry_after is not None:
                    wait_seconds = max(1.0, float(retry_after))
                else:
                    wait_seconds = min(30.0, 2**attempt)
                logger.warning("graph_retry", extra={"status": resp.status_code, "wait_s": wait_seconds})
                await asyncio.sleep(wait_seconds)
                continue

            resp.raise_for_status()
            return resp.json() if expect_json else resp.content

        resp.raise_for_status()
        return resp.json() if expect_json else resp.content

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params, expect_json=True)

    async def _get_bytes(self, path_or_url: str) -> bytes:
        return await self._request("GET", path_or_url, expect_json=False)

    async def list_items_paged(
        self, path: str, params: dict[str, Any] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        data = await self._get(path, params)
        yield data
        while "@odata.nextLink" in data:
            data = await self._get(data["@odata.nextLink"])
            yield data

    async def close(self) -> None:
        await self._client.aclose()
