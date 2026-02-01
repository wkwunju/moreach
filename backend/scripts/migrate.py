#!/usr/bin/env python3
"""
Smart database migration script.

This script handles all migration scenarios automatically:
1. Fresh database (no tables) → Run all migrations
2. Existing database from create_all() (no alembic_version) → Stamp as baseline, then upgrade
3. Already migrated database → Run pending migrations

Locking is handled in alembic/env.py using PostgreSQL advisory locks.

Usage:
    python scripts/migrate.py

This is the ONLY way to run migrations in production.
"""
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from alembic.config import Config
from alembic import command

from app.core.db import engine
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_alembic_config():
    """Get Alembic configuration."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini = os.path.join(base_dir, 'alembic.ini')

    config = Config(alembic_ini)
    config.set_main_option('sqlalchemy.url', settings.database_url)
    return config


def has_alembic_version_table() -> bool:
    """Check if alembic_version table exists."""
    inspector = inspect(engine)
    return 'alembic_version' in inspector.get_table_names()


def has_existing_tables() -> bool:
    """Check if any application tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return 'users' in tables or 'reddit_campaigns' in tables


def get_current_revision() -> str | None:
    """Get current alembic revision from database."""
    if not has_alembic_version_table():
        return None

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        return row[0] if row else None


def run_migrations():
    """
    Run database migrations with smart detection.
    Locking is handled by alembic/env.py.
    """
    config = get_alembic_config()

    has_alembic = has_alembic_version_table()
    has_tables = has_existing_tables()
    current_rev = get_current_revision()

    logger.info(f"Migration state check:")
    logger.info(f"  - alembic_version table exists: {has_alembic}")
    logger.info(f"  - application tables exist: {has_tables}")
    logger.info(f"  - current revision: {current_rev or 'None'}")

    if has_alembic and current_rev:
        logger.info("Database is under migration control. Running pending migrations...")
        command.upgrade(config, "head")
        logger.info("Migrations complete.")

    elif has_tables and not has_alembic:
        logger.info("Existing database detected without migration tracking.")
        logger.info("Stamping database as baseline (0001)...")
        command.stamp(config, "0001")
        logger.info("Running any pending migrations after baseline...")
        command.upgrade(config, "head")
        logger.info("Migrations complete.")

    else:
        logger.info("Fresh database detected. Running all migrations...")
        command.upgrade(config, "head")
        logger.info("Migrations complete.")

    final_rev = get_current_revision()
    logger.info(f"Final database revision: {final_rev}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting database migration")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'sqlite'}")
    logger.info("=" * 60)

    try:
        run_migrations()
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
