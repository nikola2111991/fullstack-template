"""
Logging Config: Structured JSON in production, human-readable in development
Usage:
    from app.logging_config import setup_logging
    setup_logging()  # call once on startup

    import logging
    logger = logging.getLogger(__name__)
    logger.info("User created", extra={"user_id": "123", "email": "test@test.com"})
"""
from __future__ import annotations
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from pydantic_settings import BaseSettings


class LogSettings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "json"  # "json" for production, "text" for development
    class Config:
        env_file = ".env"


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        # Include extra fields (request_id, user_id, etc.)
        for key in ("request_id", "user_id", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"{color}{timestamp} [{record.levelname:>8}]{self.RESET} {record.name}: {record.getMessage()}"


def setup_logging() -> None:
    """Configure logging based on environment. Call once on app startup."""
    settings = LogSettings()

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
