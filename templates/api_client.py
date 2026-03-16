"""
Python Async API Client — httpx + tenacity retry
Usage:
    async with ExternalApiClient("https://api.example.com") as api:
        result = await api.get("/users")
        if result.ok: print(result.data)
"""
from __future__ import annotations
import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any


class ApiResponse(BaseModel):
    data: Any | None = None
    error: str | None = None
    status: int = 200

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status < 300


class ExternalApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0, headers: dict[str, str] | None = None):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers or {})

    async def __aenter__(self): return self
    async def __aexit__(self, *args): await self.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
           retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)))
    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    async def _safe(self, method: str, path: str, **kwargs) -> ApiResponse:
        try:
            resp = await self._request(method, path, **kwargs)
            return ApiResponse(data=resp.json(), status=resp.status_code)
        except httpx.HTTPStatusError as e:
            return ApiResponse(error=str(e), status=e.response.status_code)
        except Exception as e:
            return ApiResponse(error=str(e), status=500)

    async def get(self, path: str, **kw) -> ApiResponse: return await self._safe("GET", path, **kw)
    async def post(self, path: str, **kw) -> ApiResponse: return await self._safe("POST", path, **kw)
    async def put(self, path: str, **kw) -> ApiResponse: return await self._safe("PUT", path, **kw)
    async def delete(self, path: str, **kw) -> ApiResponse: return await self._safe("DELETE", path, **kw)
    async def close(self): await self.client.aclose()
