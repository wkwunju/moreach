import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import Base, engine
from app.core.logging import setup_logging
from app.api.v1.routes import router as api_router
# Import all models so SQLAlchemy knows about them before create_all()
from app.models import tables  # noqa: F401


setup_logging()
logger = logging.getLogger(__name__)

# Database initialization strategy:
# - USE_ALEMBIC=true: Skip create_all, rely on Alembic migrations (production)
# - USE_ALEMBIC=false or not set: Use create_all (local development)
if os.getenv("USE_ALEMBIC", "false").lower() == "true":
    logger.info("USE_ALEMBIC=true, skipping create_all(). Run 'alembic upgrade head' to apply migrations.")
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
