"""
Error handling middleware for Disease-Relater API.

Provides custom exception handlers for consistent error responses
and security (prevents information leakage).
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

from api.validation import sanitize_error_message

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API-specific errors."""

    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error - invalid input parameters."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message, status_code=status.HTTP_404_NOT_FOUND, details=details
        )


class DatabaseError(APIError):
    """Database query/connection error."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details
        )


def setup_exception_handlers(app):
    """Configure exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """Handle custom API errors."""
        logger.warning(f"API error: {exc.message} (status={exc.status_code})")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": sanitize_error_message(exc.message),
                    "details": exc.details,
                    "status_code": exc.status_code,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")

        # Sanitize validation errors
        errors = []
        for error in exc.errors():
            sanitized_error = {
                "field": error.get("loc", ["unknown"])[-1],
                "message": error.get("msg", "Validation failed"),
                "type": error.get("type", "unknown"),
            }
            errors.append(sanitized_error)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "ValidationError",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                    "status_code": 422,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        logger.exception(f"Unhandled exception: {str(exc)}")

        # Sanitize the error message to prevent info leakage
        safe_message = "An internal server error occurred"

        # In debug mode, include more details
        from api.config import get_settings

        settings = get_settings()

        details = {}
        if settings.debug:
            details["debug_info"] = str(exc)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": safe_message,
                    "details": details,
                    "status_code": 500,
                }
            },
        )
