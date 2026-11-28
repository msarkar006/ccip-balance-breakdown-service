"""Central error handlers: every public error is `{"detail": "..."}`; 404/405 map to one safe 404."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import DomainError, RateLimitedError
from app.middleware.correlation import HEADER_NAME

logger = logging.getLogger("app.errors")

SAFE_NOT_FOUND = "Resource not found"
SAFE_SERVER_ERROR = "Internal server error"
SAFE_VALIDATION = "Request validation failed"


def _response(request: Request, status: int, detail: str, headers: dict[str, str] | None = None) -> JSONResponse:
    out = dict(headers or {})
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        out[HEADER_NAME] = correlation_id
    return JSONResponse(status_code=status, content={"detail": detail}, headers=out)


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        return await _unhandled_error(request, exc)
    if exc.status_code >= 500:
        logger.error("domain_error type=%s", type(exc).__name__)
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    if isinstance(exc, RateLimitedError):
        headers = {"Retry-After": str(exc.retry_after)}
    return _response(request, exc.status_code, exc.public_detail, headers)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await _unhandled_error(request, exc)
    if exc.status_code in (404, 405):
        return _response(request, 404, SAFE_NOT_FOUND)
    if exc.status_code == 401:
        return _response(request, 401, "Authentication required", {"WWW-Authenticate": "Bearer"})
    if exc.status_code == 403:
        return _response(request, 403, "Not permitted")
    if exc.status_code >= 500:
        return _response(request, exc.status_code, SAFE_SERVER_ERROR)
    return _response(request, exc.status_code, "Request could not be processed")


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await _unhandled_error(request, exc)
    names = sorted({str(err["loc"][-1]) for err in exc.errors() if err.get("loc")})
    detail = f"Invalid value for parameter {', '.join(names)}" if names else SAFE_VALIDATION
    return _response(request, 422, detail[:200])


async def _database_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("database_error type=%s", type(exc).__name__)
    return _response(request, 500, SAFE_SERVER_ERROR)


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error type=%s", type(exc).__name__)
    return _response(request, 500, SAFE_SERVER_ERROR)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(SQLAlchemyError, _database_error)
    app.add_exception_handler(Exception, _unhandled_error)
