"""Application factory. Every router is included here, with the API prefix applied in one place."""

from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.middleware.correlation import CorrelationIdMiddleware, CorrelationLogFilter
from app.middleware.error_handlers import register_error_handlers
from app.middleware.metrics import MetricsMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import accounts, auth, balances, data_rights, health, payments, tracking, transactions

API_PREFIX = "/api/v1"

# Routers served under the API prefix. Later tasks append their router modules here.
API_ROUTERS: list[APIRouter] = [
    auth.router,
    accounts.router,
    balances.router,
    transactions.router,
    payments.router,
    tracking.router,
    data_rights.router,
]
# Routers served at the root (health and readiness only).
ROOT_ROUTERS: list[APIRouter] = [health.router]


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if not any(isinstance(f, CorrelationLogFilter) for h in root.handlers for f in h.filters):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s correlation_id=%(correlation_id)s %(message)s")
        )
        handler.addFilter(CorrelationLogFilter())
        root.handlers = [handler]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Credit-Card Servicing Prototype (Information Only)",
        version="1.0.0",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    # add_middleware wraps: last added is outermost. Order outermost-first:
    # correlation, metrics, security headers, CORS, routing.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    register_error_handlers(app)

    for router in ROOT_ROUTERS:
        app.include_router(router)
    for router in API_ROUTERS:
        app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
