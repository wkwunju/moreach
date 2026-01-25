"""
Database Migration Script
Adds new analytics fields to the Influencer table

Run this script to add the new columns to your existing database:
    python backend/scripts/migrate_add_analytics.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import engine
from app.models.tables import Base


def migrate():
    print("Starting migration: Adding analytics fields to Influencer table")
    
    with engine.connect() as conn:
        # Check if columns exist before adding them
        columns_to_add = [
            ("avg_video_views", "FLOAT DEFAULT 0"),
            ("highest_likes", "FLOAT DEFAULT 0"),
            ("highest_comments", "FLOAT DEFAULT 0"),
            ("highest_video_views", "FLOAT DEFAULT 0"),
            ("post_sharing_percentage", "FLOAT DEFAULT 0"),
            ("post_collaboration_percentage", "FLOAT DEFAULT 0"),
            ("audience_analysis", "TEXT DEFAULT ''"),
            ("collaboration_opportunity", "TEXT DEFAULT ''"),
            ("email", "VARCHAR(256) DEFAULT ''"),
            ("external_url", "VARCHAR(512) DEFAULT ''"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                print(f"Adding column: {column_name}")
                conn.execute(text(f"ALTER TABLE influencers ADD COLUMN {column_name} {column_type}"))
                conn.commit()
                print(f"✓ Added {column_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⊙ Column {column_name} already exists, skipping")
                else:
                    print(f"✗ Error adding {column_name}: {e}")
                    raise
    
    print("\n✓ Migration complete!")
    print("\nNew fields added:")
    print("  - avg_video_views: Average video views")
    print("  - highest_likes: Peak like count")
    print("  - highest_comments: Peak comment count")
    print("  - highest_video_views: Peak video views")
    print("  - post_sharing_percentage: % of posts that are reshares")
    print("  - post_collaboration_percentage: % of posts with collaborations")
    print("  - audience_analysis: LLM-generated audience insights")
    print("  - collaboration_opportunity: LLM-generated collab potential")
    print("  - email: Contact email")
    print("  - external_url: External link from profile")


if __name__ == "__main__":
    migrate()

