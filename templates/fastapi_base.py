"""
FastAPI App Factory: Config, response models, error handlers, health check
Usage: from app.main import create_app; app = create_app()
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "my-api"
    debug: bool = False
    version: str = "1.0.0"
    database_url: str = ""
    redis_url: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _meta() -> dict[str, str]:
    return {"timestamp": datetime.now(timezone.utc).isoformat(), "request_id": str(uuid.uuid4())}


def ok(data: Any) -> dict:
    return {"data": data, "error": None, "meta": _meta()}


def err(code: str, message: str, field: str | None = None) -> dict:
    return {"data": None, "error": {"code": code, "message": message, "field": field}, "meta": _meta()}


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exc(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=err("HTTP_ERROR", exc.detail))

    @app.exception_handler(Exception)
    async def general_exc(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=err("INTERNAL_ERROR", "Unexpected error"))

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "version": settings.version}

    return app
