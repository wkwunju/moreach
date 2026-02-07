import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from app.core.config import settings
from app.core.db import Base, engine
from app.core.logging import setup_logging
from app.api.v1.routes import router as api_router
# Import all models so SQLAlchemy knows about them before create_all()
from app.models import tables  # noqa: F401


setup_logging()
logger = logging.getLogger(__name__)


def ensure_schema_updates():
    """Ensure required schema updates exist (replaces complex migrations)."""
    try:
        with engine.connect() as conn:
            # Check and add is_blocked column if missing
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'is_blocked'
            """))
            if not result.fetchone():
                logger.info("Adding is_blocked column to users table...")
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_blocked BOOLEAN NOT NULL DEFAULT false"
                ))
                conn.commit()
                logger.info("is_blocked column added successfully")
            else:
                logger.info("Schema is up to date")
    except Exception as e:
        logger.error(f"Error ensuring schema updates: {e}")


# Database initialization
if os.getenv("USE_ALEMBIC", "false").lower() != "true":
    logger.info("Running create_all() for database initialization")
    Base.metadata.create_all(bind=engine)

# Always ensure schema is up to date (handles missing columns)
ensure_schema_updates()

app = FastAPI(title=settings.app_name)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://moreach.ai",
    "https://www.moreach.ai",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
