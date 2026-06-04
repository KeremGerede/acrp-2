import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import create_tables
from app.db.migrations import run_migrations

# Import all models so SQLAlchemy registers them before create_tables()
import app.models  # noqa: F401

from app.api.routes import (
    tenants,
    integrations,
    review_rules,
    functional_test_configs,
    events,
    merge_reviews,
    functional_tests,
    promotions,
    notifications,
    stats,
    webhooks,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic DevOps Platform",
    description="Corporate multi-tenant AI code review and functional test reporting platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    logger.info("Creating database tables...")
    create_tables()
    logger.info("Running schema migrations...")
    run_migrations()
    logger.info("Database ready.")


@app.get("/api/debug/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


app.include_router(tenants.router)
app.include_router(integrations.router)
app.include_router(review_rules.router)
app.include_router(functional_test_configs.router)
app.include_router(events.router)
app.include_router(merge_reviews.router)
app.include_router(functional_tests.router)
app.include_router(promotions.router)
app.include_router(notifications.router)
app.include_router(stats.router)
app.include_router(webhooks.router)
