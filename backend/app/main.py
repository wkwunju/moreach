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


def ensure_is_blocked_column():
    """Fallback: ensure is_blocked column exists in users table."""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'is_blocked' not in columns:
            logger.warning("is_blocked column missing, adding it now...")
            with engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_blocked BOOLEAN NOT NULL DEFAULT false"
                ))
                conn.commit()
            logger.info("is_blocked column added successfully")
        else:
            logger.info("is_blocked column already exists")
    except Exception as e:
        logger.error(f"Error checking/adding is_blocked column: {e}")


# Database initialization strategy:
# - USE_ALEMBIC=true: Skip create_all, rely on Alembic migrations (production)
# - USE_ALEMBIC=false or not set: Use create_all (local development)
if os.getenv("USE_ALEMBIC", "false").lower() == "true":
    logger.info("USE_ALEMBIC=true, skipping create_all(). Run 'alembic upgrade head' to apply migrations.")
    # Fallback: ensure critical columns exist even if migration failed
    ensure_is_blocked_column()
else:
    logger.info("Using create_all() for database initialization (set USE_ALEMBIC=true for Alembic)")
    Base.metadata.create_all(bind=engine)

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
