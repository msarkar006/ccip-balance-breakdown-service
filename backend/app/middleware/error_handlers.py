"""
Global error handlers for the application.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global error handlers on the FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle application-specific errors."""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.warning(
            "Application error",
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id,
            path=request.url.path
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "correlation_id": correlation_id
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.warning(
            "Validation error",
            errors=exc.errors(),
            correlation_id=correlation_id,
            path=request.url.path
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "correlation_id": correlation_id
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.error(
            "Unexpected error",
            error=str(exc),
            error_type=type(exc).__name__,
            correlation_id=correlation_id,
            path=request.url.path,
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id
            }
        )
