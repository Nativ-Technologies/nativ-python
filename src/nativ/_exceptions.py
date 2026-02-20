"""Nativ SDK exception hierarchy."""

from __future__ import annotations

from typing import Any, Dict, Optional


class NativError(Exception):
    """Base exception for all Nativ SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(NativError):
    """Invalid or missing API key (HTTP 401)."""


class InsufficientCreditsError(NativError):
    """Not enough credits for the operation (HTTP 402).

    Top up at https://dashboard.usenativ.com
    """


class ValidationError(NativError):
    """Invalid request parameters (HTTP 400 / 422)."""


class NotFoundError(NativError):
    """Resource not found (HTTP 404)."""


class RateLimitError(NativError):
    """Too many requests (HTTP 429)."""


class ServerError(NativError):
    """Nativ API returned a server-side error (HTTP 5xx)."""
