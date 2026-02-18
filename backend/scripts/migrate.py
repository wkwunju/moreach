#!/usr/bin/env python3
"""
Smart database migration script for Railway deployment.

This script handles all migration scenarios automatically:
1. Fresh database (no tables) → Run all migrations
2. Existing database from create_all() (no alembic_version) → Stamp as baseline, then upgrade
3. Already migrated database → Run pending migrations

Uses retry + idempotent checks to handle concurrent deployment instances.
Advisory locks don't work with PgBouncer (transaction mode), so we use a
try/verify approach instead: attempt the migration, and if it fails, check
if another instance already completed it.

Usage:
    python scripts/migrate.py
"""
import os
import sys
import time
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

# Maximum retries for concurrent migration conflicts
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def get_alembic_config():
    """Get Alembic configuration."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini = os.path.join(base_dir, 'alembic.ini')

    config = Config(alembic_ini)
    config.set_main_option('sqlalchemy.url', settings.database_url)
    return config


def get_alembic_head(config):
    """Get the latest (head) revision from Alembic's script directory."""
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def check_db_state(conn):
    """Check current database migration state. Returns (has_alembic, has_tables, current_rev)."""
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

    return has_alembic, has_tables, current_rev


def detect_schema_level(conn, has_tables):
    """Detect what migration level the actual schema is at.

    Each migration adds specific schema artifacts. Check from newest to oldest:
      0007: reddit_campaigns.custom_comment_prompt column
      0006: subreddit_cache.rules_json column
      0005: users.last_login_at column
      0004: poll_jobs table + reddit_leads.poll_job_id column
      0003: users.is_blocked column
      0002: usage_tracking table
      0001: baseline (users table exists)
    """
    if not has_tables:
        return None

    result = conn.execute(text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'reddit_campaigns' AND column_name = 'custom_comment_prompt')"
    ))
    has_custom_prompts = result.scalar()

    result = conn.execute(text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'subreddit_cache' AND column_name = 'rules_json')"
    ))
    has_rules_json = result.scalar()

    result = conn.execute(text(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'last_login_at')"
    ))
    has_last_login_at = result.scalar()

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

    logger.info(f"  - custom_comment_prompt column exists: {has_custom_prompts}")
    logger.info(f"  - rules_json column exists: {has_rules_json}")
    logger.info(f"  - last_login_at column exists: {has_last_login_at}")
    logger.info(f"  - poll_jobs table exists: {has_poll_jobs}")
    logger.info(f"  - usage_tracking table exists: {has_usage_tracking}")
    logger.info(f"  - is_blocked column exists: {has_is_blocked}")

    if has_custom_prompts:
        return "0007"
    elif has_rules_json:
        return "0006"
    elif has_last_login_at:
        return "0005"
    elif has_poll_jobs:
        return "0004"
    elif has_is_blocked:
        return "0003"
    elif has_usage_tracking:
        return "0002"
    elif has_tables:
        return "0001"
    return None


def run_migrations():
    """
    Run database migrations with retry logic for concurrent deployments.

    Strategy: attempt migration, if it fails check whether another instance
    already completed it. All migration DDL is idempotent (IF NOT EXISTS checks).
    """
    config = get_alembic_config()
    head_rev = get_alembic_head(config)
    logger.info(f"Alembic head revision: {head_rev}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                has_alembic, has_tables, current_rev = check_db_state(conn)
                actual_level = detect_schema_level(conn, has_tables)

                logger.info(f"Migration state check:")
                logger.info(f"  - alembic_version table exists: {has_alembic}")
                logger.info(f"  - application tables exist: {has_tables}")
                logger.info(f"  - current revision: {current_rev or 'None'}")
                logger.info(f"  - actual schema level: {actual_level or 'None'}")

                # Already at head - nothing to do
                if current_rev == head_rev:
                    logger.info(f"Already at head revision ({head_rev}). No migration needed.")
                    return

            # Run migration (Alembic opens its own connection via env.py)
            if has_alembic and current_rev:
                # Schema might be ahead of recorded revision (e.g. create_all ran)
                if actual_level and actual_level > current_rev:
                    logger.info(f"Schema is at {actual_level} but revision says {current_rev}. Re-stamping...")
                    command.stamp(config, actual_level)
                logger.info("Database is under migration control. Running pending migrations...")
                command.upgrade(config, "head")

            elif has_tables:
                # Tables exist but no alembic tracking
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

            # Verify migration completed
            with engine.connect() as conn:
                _, _, final_rev = check_db_state(conn)
                logger.info(f"Migrations complete. Final revision: {final_rev}")
            return

        except Exception as e:
            logger.warning(f"Migration attempt {attempt}/{MAX_RETRIES} failed: {e}")

            # Check if another instance already completed the migration
            try:
                with engine.connect() as conn:
                    _, _, current_rev = check_db_state(conn)
                    if current_rev == head_rev:
                        logger.info(
                            f"Migration already completed by another instance "
                            f"(revision: {current_rev}). Proceeding to start app."
                        )
                        return
            except Exception:
                pass  # DB might be temporarily unavailable

            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error("All migration attempts failed.")
                raise


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
