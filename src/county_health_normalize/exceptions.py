"""Faults for a county rate that cannot be published."""

from __future__ import annotations


class EngineKernelException(Exception):
    """Raised when a county record breaks the rate contract."""

    def __init__(self, message: str, *, fatal: bool = True) -> None:
        super().__init__(message)
        self.fatal = fatal
