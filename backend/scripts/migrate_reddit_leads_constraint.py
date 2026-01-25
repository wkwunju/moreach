"""
数据库迁移脚本：修改 reddit_leads 表的唯一约束

问题：原来的约束是 reddit_post_id 全局唯一，
     但业务逻辑需要 (campaign_id, reddit_post_id) 复合唯一。

运行方式：
    cd backend
    python -m scripts.migrate_reddit_leads_constraint

注意：运行前请先备份数据库！
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


def migrate():
    # 数据库路径
    db_path = Path(__file__).parent.parent / "app.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    # 备份数据库
    backup_path = db_path.parent / f"app.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup at {backup_path}")
    shutil.copy(db_path, backup_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration...")

        # 1. 检查当前表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reddit_leads'")
        result = cursor.fetchone()
        if not result:
            print("Table 'reddit_leads' not found")
            return

        print(f"Current table structure:\n{result[0]}\n")

        # 2. 检查是否有重复的 reddit_post_id（跨不同 campaign）
        cursor.execute("""
            SELECT reddit_post_id, COUNT(*) as cnt
            FROM reddit_leads
            GROUP BY reddit_post_id
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"Warning: Found {len(duplicates)} duplicate reddit_post_id values")
            print("These will cause issues. Please review and clean up first.")
            for dup in duplicates[:5]:
                print(f"  - {dup[0]}: {dup[1]} occurrences")
            return

        # 3. 创建新表（带复合唯一约束）
        print("Creating new table structure...")
        cursor.execute("""
            CREATE TABLE reddit_leads_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                reddit_post_id VARCHAR(128) NOT NULL,
                subreddit_name VARCHAR(128) NOT NULL,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                author VARCHAR(128) NOT NULL,
                post_url VARCHAR(512) NOT NULL,
                score INTEGER DEFAULT 0,
                num_comments INTEGER DEFAULT 0,
                created_utc FLOAT NOT NULL,
                relevancy_score FLOAT,
                relevancy_reason TEXT DEFAULT '',
                suggested_comment TEXT DEFAULT '',
                suggested_dm TEXT DEFAULT '',
                status VARCHAR(16) DEFAULT 'NEW',
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES reddit_campaigns(id),
                UNIQUE (campaign_id, reddit_post_id)
            )
        """)

        # 4. 复制数据
        print("Copying data to new table...")
        cursor.execute("""
            INSERT INTO reddit_leads_new
            SELECT * FROM reddit_leads
        """)

        rows_copied = cursor.rowcount
        print(f"Copied {rows_copied} rows")

        # 5. 删除旧表
        print("Dropping old table...")
        cursor.execute("DROP TABLE reddit_leads")

        # 6. 重命名新表
        print("Renaming new table...")
        cursor.execute("ALTER TABLE reddit_leads_new RENAME TO reddit_leads")

        # 7. 重新创建索引
        print("Creating index on reddit_post_id...")
        cursor.execute("CREATE INDEX ix_reddit_leads_reddit_post_id ON reddit_leads (reddit_post_id)")

        # 8. 提交事务
        conn.commit()
        print("\nMigration completed successfully!")

        # 验证新结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reddit_leads'")
        result = cursor.fetchone()
        print(f"\nNew table structure:\n{result[0]}")

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        print(f"Database restored from backup at {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
