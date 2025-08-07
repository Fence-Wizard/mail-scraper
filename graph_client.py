# graph_client.py
import httpx
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
from typing import Any, AsyncGenerator, Dict
from fetch_config import settings

GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

class GraphClient:
    def __init__(self):
        self._token: str = None
        self._client = httpx.AsyncClient(timeout=30)

    async def authenticate(self) -> None:
        """Acquire a token via client credentials."""
        url = f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }
        resp = await self._client.post(url, data=data)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]

    async def _get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self._token:
            await self.authenticate()
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = await self._client.get(GRAPH_ENDPOINT + path, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

    async def list_items_paged(self, path: str, params: Dict[str, Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield each page’s JSON, following @odata.nextLink."""
        data = await self._get(path, params)
        yield data
        while "@odata.nextLink" in data:
            data = await self._get(data["@odata.nextLink"].replace(GRAPH_ENDPOINT, ""), None)
            yield data
