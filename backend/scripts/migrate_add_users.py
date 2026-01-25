"""
Migration script to add users table
Run this with: python scripts/migrate_add_users.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import engine

def migrate():
    """Add users table to database"""
    
    # Create users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(256) UNIQUE NOT NULL,
        hashed_password VARCHAR(256) NOT NULL,
        full_name VARCHAR(256) DEFAULT '',
        company VARCHAR(256) DEFAULT '',
        job_title VARCHAR(256) DEFAULT '',
        industry VARCHAR(50) DEFAULT 'Other',
        usage_type VARCHAR(50) DEFAULT 'Personal Use',
        role VARCHAR(20) DEFAULT 'USER',
        is_active BOOLEAN DEFAULT 1,
        email_verified BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Create index on email
    create_email_index = """
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """
    
    with engine.connect() as conn:
        print("Creating users table...")
        conn.execute(text(create_users_table))
        conn.commit()
        
        print("Creating email index...")
        conn.execute(text(create_email_index))
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("Users table created with the following fields:")
        print("  - id, email, hashed_password")
        print("  - full_name, company, job_title")
        print("  - industry, usage_type")
        print("  - role, is_active, email_verified")
        print("  - created_at, updated_at")

if __name__ == "__main__":
    migrate()

