"""
FastAPI Middleware — Request ID, logging, rate limiting, auth
Usage: setup_middleware(app) in create_app()
"""
from __future__ import annotations
import time, uuid, logging
from collections import defaultdict
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        logger.info(f"{request.method} {request.url.path} {response.status_code} {round((time.time()-start)*1000, 2)}ms")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests=100, window_seconds=60):
        super().__init__(app)
        self.max_requests, self.window_seconds = max_requests, window_seconds
        self.store = defaultdict(lambda: {"count": 0, "reset": 0})

    async def dispatch(self, request, call_next):
        if request.url.path == "/health": return await call_next(request)
        ip = request.client.host if request.client else "anon"
        now, entry = time.time(), self.store[ip]
        if now > entry["reset"]: entry["count"], entry["reset"] = 0, now + self.window_seconds
        entry["count"] += 1
        if entry["count"] > self.max_requests:
            return JSONResponse(status_code=429, content={"error": "Rate limited"}, headers={"Retry-After": str(int(entry["reset"]-now))})
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - entry["count"]))
        return response


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(key: str | None = Security(api_key_header)) -> str:
    if not key: raise HTTPException(401, "API key required")
    return key

def setup_middleware(app):
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
