"""API client for FPL data."""

from fpl.api.client import FPLClient
from fpl.api.endpoints import ENDPOINTS
from fpl.api.exceptions import (
    FPLAPIError,
    NotFoundError,
    RateLimitError,
)

__all__ = [
    "FPLClient",
    "ENDPOINTS",
    "FPLAPIError",
    "NotFoundError",
    "RateLimitError",
]
