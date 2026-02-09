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
    Uses pg_try_advisory_lock - if another instance holds the lock, skip and let app start.
    """
    config = get_alembic_config()

    with engine.connect() as conn:
        # Try to acquire lock - non-blocking
        result = conn.execute(text(f"SELECT pg_try_advisory_lock({MIGRATION_LOCK_ID})"))
        got_lock = result.scalar()

        if not got_lock:
            logger.info("Another instance is running migrations. Waiting for completion...")
            # Wait for the lock (meaning other migration finished)
            conn.execute(text(f"SELECT pg_advisory_lock({MIGRATION_LOCK_ID})"))
            conn.execute(text(f"SELECT pg_advisory_unlock({MIGRATION_LOCK_ID})"))
            logger.info("Other migration completed. Proceeding to start app.")
            return

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

            # Detect actual schema state regardless of alembic_version
            def detect_schema_level():
                """Detect what migration level the actual schema is at.

                Each migration adds specific schema artifacts. Check from newest to oldest:
                  0004: poll_jobs table + reddit_leads.poll_job_id column
                  0003: users.is_blocked column
                  0002: usage_tracking table
                  0001: baseline (users table exists)
                """
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'poll_jobs')"
                ))
                has_poll_jobs = result.scalar()

                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'users' AND column_name = 'is_blocked')"
                ))
                has_is_blocked = result.scalar()

                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'usage_tracking')"
                ))
                has_usage_tracking = result.scalar()

                logger.info(f"  - poll_jobs table exists: {has_poll_jobs}")
                logger.info(f"  - usage_tracking table exists: {has_usage_tracking}")
                logger.info(f"  - is_blocked column exists: {has_is_blocked}")

                if has_poll_jobs:
                    return "0004"
                elif has_is_blocked:
                    return "0003"
                elif has_usage_tracking:
                    return "0002"
                elif has_tables:
                    return "0001"
                return None

            if has_tables:
                actual_level = detect_schema_level()
            else:
                actual_level = None

            if has_alembic and current_rev:
                # Schema might be ahead of recorded revision (e.g. create_all ran)
                if actual_level and actual_level > current_rev:
                    logger.info(f"Schema is at {actual_level} but revision says {current_rev}. Re-stamping...")
                    command.stamp(config, actual_level)
                # Now run any pending migrations from actual level to head
                logger.info("Database is under migration control. Running pending migrations...")
                command.upgrade(config, "head")

            elif has_tables:
                # Tables exist but either no alembic table or empty alembic_version
                logger.info("Existing database detected. Syncing migration tracking to schema state...")
                if actual_level:
                    logger.info(f"Stamping at {actual_level}...")
                    command.stamp(config, actual_level)
                    command.upgrade(config, "head")
                else:
                    logger.info("Stamping at 0001, then upgrading...")
                    command.stamp(config, "0001")
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
