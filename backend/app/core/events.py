"""
Application startup and shutdown event handlers.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

import app.models  # noqa: F401 - Ensure all models are imported
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager - handles startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None during application runtime
    """
    # Startup
    logger.info("Application starting up")
    configure_logging()

    yield

    # Shutdown
    logger.info("Application shutting down")
