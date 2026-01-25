"""
Migration script to add user_id to reddit_campaigns table
Run this with: python scripts/migrate_add_user_to_campaigns.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import engine

def migrate():
    """Add user_id column to reddit_campaigns table"""
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(reddit_campaigns)"))
        columns = [row[1] for row in result]
        
        if 'user_id' in columns:
            print("✅ user_id column already exists in reddit_campaigns table")
            return
        
        print("Adding user_id column to reddit_campaigns table...")
        
        # Add user_id column (nullable for existing campaigns)
        conn.execute(text("""
            ALTER TABLE reddit_campaigns 
            ADD COLUMN user_id INTEGER
        """))
        conn.commit()
        
        # Create index on user_id for better query performance
        print("Creating index on user_id...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reddit_campaigns_user_id 
            ON reddit_campaigns(user_id)
        """))
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("Notes:")
        print("  - user_id column added to reddit_campaigns")
        print("  - Existing campaigns will have NULL user_id")
        print("  - New campaigns will require user_id")
        print("  - Index created on user_id for better performance")

if __name__ == "__main__":
    migrate()

