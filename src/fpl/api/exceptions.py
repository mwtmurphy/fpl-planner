"""Custom exceptions for FPL API operations."""


class FPLAPIError(Exception):
    """Base exception for FPL API errors."""

    pass


class NotFoundError(FPLAPIError):
    """Raised when requested resource is not found (404)."""

    pass


class RateLimitError(FPLAPIError):
    """Raised when API rate limit is exceeded."""

    pass


class ServerError(FPLAPIError):
    """Raised when FPL API returns server error (500)."""

    pass
