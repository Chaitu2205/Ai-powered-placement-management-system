"""
Exceptions raised by the AI layer. All are AppException subclasses so the
existing global exception handlers (app/utils/exceptions.py) turn them into
clean JSON responses - an AI failure never crashes the app or leaks a raw
stack trace/provider error to the client.
"""
from fastapi import status as http_status

from app.utils.exceptions import AppException


class AIConfigurationError(AppException):
    """Raised when an AI feature is requested but AI_API_KEY isn't set."""
    def __init__(self, message: str = "AI features are not configured on this server"):
        super().__init__(message, status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE)


class AIProviderError(AppException):
    """Raised when the AI provider itself fails (network, timeout, rate limit, API error)."""
    def __init__(self, message: str = "The AI service is temporarily unavailable. Please try again."):
        super().__init__(message, status_code=http_status.HTTP_502_BAD_GATEWAY)


class AIResponseValidationError(AppException):
    """Raised when the AI provider returns something that doesn't match our expected structure."""
    def __init__(self, message: str = "The AI service returned an unexpected response. Please try again."):
        super().__init__(message, status_code=http_status.HTTP_502_BAD_GATEWAY)
