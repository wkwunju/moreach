#!/usr/bin/env python3
"""
Smart database migration script with distributed locking.

This script handles all migration scenarios automatically:
1. Fresh database (no tables) → Run all migrations
2. Existing database from create_all() (no alembic_version) → Stamp as baseline, then upgrade
3. Already migrated database → Run pending migrations

Uses PostgreSQL advisory locks to prevent concurrent migrations.

Usage:
    python scripts/migrate.py

This is the ONLY way to run migrations in production.
"""
import os
import sys
import logging
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from alembic.config import Config
from alembic import command

from app.core.db import engine
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Advisory lock ID for migrations (any unique integer)
MIGRATION_LOCK_ID = 123456789


def get_alembic_config():
    """Get Alembic configuration."""
    # Find alembic.ini relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini = os.path.join(base_dir, 'alembic.ini')

    config = Config(alembic_ini)
    config.set_main_option('sqlalchemy.url', settings.database_url)
    return config


def has_alembic_version_table() -> bool:
    """Check if alembic_version table exists (indicates DB is already under migration control)."""
    inspector = inspect(engine)
    return 'alembic_version' in inspector.get_table_names()


def has_existing_tables() -> bool:
    """Check if any application tables exist (e.g., users table)."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    # Check for core tables that should exist if DB was created by create_all()
    return 'users' in tables or 'reddit_campaigns' in tables


def get_current_revision() -> str | None:
    """Get current alembic revision from database."""
    if not has_alembic_version_table():
        return None

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        return row[0] if row else None


def acquire_migration_lock(conn, timeout_seconds: int = 30) -> bool:
    """
    Try to acquire an advisory lock for migrations.
    Returns True if lock acquired, False if another process holds it.
    """
    # pg_try_advisory_lock returns true if lock acquired, false otherwise
    result = conn.execute(
        text(f"SELECT pg_try_advisory_lock({MIGRATION_LOCK_ID})")
    )
    return result.scalar()


def release_migration_lock(conn):
    """Release the advisory lock."""
    conn.execute(text(f"SELECT pg_advisory_unlock({MIGRATION_LOCK_ID})"))


def wait_for_lock(conn, max_wait_seconds: int = 60) -> bool:
    """Wait for migration lock with timeout."""
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        if acquire_migration_lock(conn):
            return True
        logger.info("Another migration in progress, waiting...")
        time.sleep(2)
    return False


def run_migrations():
    """
    Run database migrations with smart detection and distributed locking.

    Uses PostgreSQL advisory locks to prevent concurrent migrations.

    Handles three scenarios:
    1. Fresh DB (no tables): Run upgrade head
    2. Existing DB without alembic_version: Stamp baseline, then upgrade
    3. Already migrated DB: Run upgrade head (only pending migrations)
    """
    config = get_alembic_config()

    # Use a connection for locking
    with engine.connect() as conn:
        # Try to acquire lock
        if not wait_for_lock(conn, max_wait_seconds=60):
            logger.warning("Could not acquire migration lock after 60s. Another migration may be running.")
            logger.info("Checking if migrations are already complete...")
            # Check if another process already completed migrations
            if has_existing_tables():
                logger.info("Tables exist. Assuming migrations completed by another process.")
                return
            else:
                raise RuntimeError("Could not acquire migration lock and tables don't exist")

        try:
            logger.info("Migration lock acquired. Starting migration...")

            has_alembic = has_alembic_version_table()
            has_tables = has_existing_tables()
            current_rev = get_current_revision()

            logger.info(f"Migration state check:")
            logger.info(f"  - alembic_version table exists: {has_alembic}")
            logger.info(f"  - application tables exist: {has_tables}")
            logger.info(f"  - current revision: {current_rev or 'None'}")

            if has_alembic and current_rev:
                # Scenario 3: Already under migration control, run any pending migrations
                logger.info("Database is under migration control. Running pending migrations...")
                command.upgrade(config, "head")
                logger.info("Migrations complete.")

            elif has_tables and not has_alembic:
                # Scenario 2: Tables exist but no alembic tracking
                # This means DB was created by create_all() - stamp as baseline
                logger.info("Existing database detected without migration tracking.")
                logger.info("Stamping database as baseline (0001)...")
                command.stamp(config, "0001")
                logger.info("Running any pending migrations after baseline...")
                command.upgrade(config, "head")
                logger.info("Migrations complete.")

            else:
                # Scenario 1: Fresh database - run all migrations
                logger.info("Fresh database detected. Running all migrations...")
                command.upgrade(config, "head")
                logger.info("Migrations complete.")

            # Verify final state
            final_rev = get_current_revision()
            logger.info(f"Final database revision: {final_rev}")

        finally:
            release_migration_lock(conn)
            logger.info("Migration lock released.")


def quick_check_migrations_needed() -> bool:
    """
    Quick check if migrations are needed at all.
    Returns False if database is already fully migrated (fast path).
    """
    try:
        if has_alembic_version_table() and has_existing_tables():
            current_rev = get_current_revision()
            if current_rev:
                logger.info(f"Database already at revision {current_rev}. Quick check passed.")
                return False
    except Exception as e:
        logger.warning(f"Quick check failed: {e}. Will proceed with full migration check.")
    return True


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting smart database migration")
    logger.info(f"Database URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'sqlite'}")
    logger.info("=" * 60)

    try:
        # Fast path: skip if already migrated
        if not quick_check_migrations_needed():
            logger.info("=" * 60)
            logger.info("No migrations needed. Database is up to date.")
            logger.info("=" * 60)
            sys.exit(0)

        run_migrations()
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
