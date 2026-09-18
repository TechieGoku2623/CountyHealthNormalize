"""Shared exceptions for the normalization pipeline."""


class CountyHealthNormalizeError(Exception):
    """Base error for this package."""


class AdapterError(CountyHealthNormalizeError):
    """Raised when a source adapter cannot interpret input data."""


class ValidationBatchError(CountyHealthNormalizeError):
    """Raised when one or more rows fail schema validation in strict mode."""

    def __init__(self, message: str, *, failures: list[str]) -> None:
        super().__init__(message)
        self.failures = failures
