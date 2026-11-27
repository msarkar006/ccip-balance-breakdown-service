"""
FastAPI application main entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.accounts import router as accounts_router
from app.auth.auth import router as auth_router
from app.balance_breakdowns.balance_breakdowns import router as balance_breakdowns_router
from app.core.events import lifespan
from app.core.settings import settings
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.error_handlers import register_error_handlers
from app.rewards_offers_instalments.rewards_offers_instalments import router as offers_router

app = FastAPI(
    title="CCIP Balance Breakdown Service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Register error handlers
register_error_handlers(app)

# Import transaction, payment, direct debit, balance transfer, and money transfer routers
from app.balance_transfers.balance_transfers import router as balance_transfers_router
from app.direct_debits.direct_debits import router as direct_debits_router
from app.money_transfers.money_transfers import payee_router
from app.money_transfers.money_transfers import router as money_transfers_router
from app.payments.payments import router as payments_router
from app.rewards_offers_instalments.rewards_offers_instalments import (
    instalments_router,
    rewards_router,
)
from app.status_tracker.status_tracker import router as status_tracker_router
from app.support_diagnostics.support_diagnostics import health_router
from app.support_diagnostics.support_diagnostics import router as support_diagnostics_router
from app.transactions.transactions import router as transactions_router

# Include routers
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(balance_breakdowns_router)
app.include_router(offers_router)
app.include_router(rewards_router)
app.include_router(instalments_router)
app.include_router(transactions_router)
app.include_router(payments_router)
app.include_router(direct_debits_router)
app.include_router(balance_transfers_router)
app.include_router(money_transfers_router)
app.include_router(payee_router)
app.include_router(status_tracker_router)
app.include_router(support_diagnostics_router)
app.include_router(health_router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "CCIP Balance Breakdown Service"}
