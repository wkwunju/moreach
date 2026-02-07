#!/usr/bin/env python3
"""
Smart database migration script with proper locking.

This script handles all migration scenarios automatically:
1. Fresh database (no tables) → Run all migrations
2. Existing database from create_all() (no alembic_version) → Stamp as baseline, then upgrade
3. Already migrated database → Run pending migrations

Uses PostgreSQL advisory lock to prevent concurrent migrations.

Usage:
    python scripts/migrate.py
"""
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from alembic.config import Config
from alembic import command

from app.core.db import engine
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Advisory lock ID - must be unique for migrations
MIGRATION_LOCK_ID = 999888777


def get_alembic_config():
    """Get Alembic configuration."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini = os.path.join(base_dir, 'alembic.ini')

    config = Config(alembic_ini)
    config.set_main_option('sqlalchemy.url', settings.database_url)
    return config


def run_migrations():
    """
    Run database migrations with advisory lock.
    All checks and migrations happen within a single locked connection.
    """
    config = get_alembic_config()

    with engine.connect() as conn:
        # Acquire advisory lock - blocks until available
        logger.info("Acquiring migration lock...")
        conn.execute(text(f"SELECT pg_advisory_lock({MIGRATION_LOCK_ID})"))
        logger.info("Migration lock acquired.")

        try:
            # Check database state INSIDE the lock
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')"
            ))
            has_alembic = result.scalar()

            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
            ))
            has_tables = result.scalar()

            current_rev = None
            if has_alembic:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                row = result.fetchone()
                current_rev = row[0] if row else None

            logger.info(f"Migration state check:")
            logger.info(f"  - alembic_version table exists: {has_alembic}")
            logger.info(f"  - application tables exist: {has_tables}")
            logger.info(f"  - current revision: {current_rev or 'None'}")

            if has_alembic and current_rev:
                logger.info("Database is under migration control. Running pending migrations...")
                command.upgrade(config, "head")

            elif has_tables and not has_alembic:
                logger.info("Existing database detected without migration tracking.")
                logger.info("Stamping database as baseline (0001)...")
                command.stamp(config, "0001")
                logger.info("Running pending migrations after baseline...")
                command.upgrade(config, "head")

            else:
                logger.info("Fresh database detected. Running all migrations...")
                command.upgrade(config, "head")

            # Get final revision
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            final_rev = row[0] if row else None
            logger.info(f"Migrations complete. Final revision: {final_rev}")

        finally:
            # Release lock
            conn.execute(text(f"SELECT pg_advisory_unlock({MIGRATION_LOCK_ID})"))
            logger.info("Migration lock released.")


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
