"""
Database Migration Script
Removes is_deleted column from reddit_campaigns table (SQLite doesn't support DROP COLUMN)
We'll recreate the table without the is_deleted column

Run this script:
    python backend/scripts/migrate_remove_is_deleted.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import engine

def migrate():
    print("Starting migration: Removing is_deleted column from reddit_campaigns table")
    print("Note: SQLite requires recreating the table to drop a column")
    
    with engine.connect() as conn:
        try:
            # Step 1: Create new table without is_deleted
            print("Step 1: Creating new table structure...")
            conn.execute(text("""
                CREATE TABLE reddit_campaigns_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'DISCOVERING',
                    business_description TEXT NOT NULL,
                    keywords TEXT DEFAULT '',
                    search_queries TEXT DEFAULT '',
                    poll_interval_hours INTEGER DEFAULT 6,
                    last_poll_at DATETIME
                )
            """))
            
            # Step 2: Copy data from old table to new table
            print("Step 2: Copying data...")
            conn.execute(text("""
                INSERT INTO reddit_campaigns_new 
                (id, created_at, updated_at, status, business_description, keywords, 
                 search_queries, poll_interval_hours, last_poll_at)
                SELECT id, created_at, updated_at, status, business_description, keywords,
                       search_queries, poll_interval_hours, last_poll_at
                FROM reddit_campaigns
            """))
            
            # Step 3: Drop old table
            print("Step 3: Dropping old table...")
            conn.execute(text("DROP TABLE reddit_campaigns"))
            
            # Step 4: Rename new table
            print("Step 4: Renaming new table...")
            conn.execute(text("ALTER TABLE reddit_campaigns_new RENAME TO reddit_campaigns"))
            
            conn.commit()
            print("✓ Migration complete!")
            print("\nRemoved is_deleted column - now using status='DELETED' instead")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate()

