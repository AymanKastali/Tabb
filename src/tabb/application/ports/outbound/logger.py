"""Outbound port — logger interface for tabb."""

from typing import Any, Protocol


class LoggerPort(Protocol):
    """Abstract logger interface (outbound port).

    Concrete logging configuration lives in the adapters layer.
    The stdlib logging.Logger satisfies this protocol structurally.
    """

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
