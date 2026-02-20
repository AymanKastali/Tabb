"""Logging adapter — Rich (dev) / JSON (prod) for tabb."""

import json
import logging
from typing import Any

from rich.logging import RichHandler

from tabb.adapters.config.settings import settings

_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message"}


def _get_extras(record: logging.LogRecord) -> dict[str, Any]:
    """Extract extra fields from a log record."""
    return {k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRS}


class _JSONFormatter(logging.Formatter):
    """JSON structured log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = _get_extras(record)
        if extras:
            log_entry["extra"] = extras
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class _RichExtraFormatter(logging.Formatter):
    """Formatter that appends extra fields to the message for Rich output."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        extras = _get_extras(record)
        if extras:
            extra_str = " ".join(f"{k}={v}" for k, v in extras.items())
            message = f"{message}  [{extra_str}]"
        return message


def setup_logging() -> None:
    """Configure root logger: RichHandler when debug, JSON otherwise."""
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    root.handlers.clear()

    if settings.debug:
        handler: logging.Handler = RichHandler(
            rich_tracebacks=True, show_time=True, show_path=False,
        )
        handler.setFormatter(_RichExtraFormatter())
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(_JSONFormatter())

    root.addHandler(handler)


logger = logging.getLogger("tabb")
