"""
Subreddit Cache Service
Manages caching of discovered subreddits to avoid duplicate API calls
and prepare data for future vector database integration.
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from sqlalchemy.orm import Session

from app.models.tables import SubredditCache


logger = logging.getLogger(__name__)


def parse_created_utc(value: Union[str, float, None]) -> Optional[float]:
    """
    Parse created_utc from Apify response.
    Apify may return ISO string like '2008-01-25T03:18:39.000Z' or float timestamp.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            # Parse ISO format: '2008-01-25T03:18:39.000Z'
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse created_utc: {value}")
            return None

    return None


class SubredditCacheService:
    """Service for managing subreddit cache"""

    def cache_subreddits(
        self,
        db: Session,
        subreddits: List[Dict[str, Any]],
        search_queries: List[str]
    ) -> int:
        """
        Cache discovered subreddits to database.

        - If subreddit exists: update info and increment discovery_count
        - If new: create new record

        Args:
            db: Database session
            subreddits: List of subreddit dicts from Apify
            search_queries: List of search queries that found these subreddits

        Returns:
            Number of subreddits cached/updated
        """
        cached_count = 0
        queries_json = json.dumps(search_queries)

        for sub in subreddits:
            name = sub.get("name", "").strip()
            if not name:
                continue

            # Check if already cached
            existing = db.query(SubredditCache).filter(
                SubredditCache.name == name
            ).first()

            if existing:
                # Update existing record
                existing.subscribers = max(existing.subscribers, sub.get("subscribers", 0))
                existing.title = sub.get("title", "") or existing.title
                existing.description = sub.get("description", "") or existing.description
                existing.url = sub.get("url", "") or existing.url
                existing.discovery_count += 1

                # Merge search queries
                try:
                    existing_queries = json.loads(existing.discovered_via_queries or "[]")
                except json.JSONDecodeError:
                    existing_queries = []

                # Add new queries that aren't already tracked
                for query in search_queries:
                    if query not in existing_queries:
                        existing_queries.append(query)

                existing.discovered_via_queries = json.dumps(existing_queries)

                logger.debug(f"Updated cached subreddit: {name} (discovery_count={existing.discovery_count})")
            else:
                # Create new cache entry
                cache_entry = SubredditCache(
                    name=name,
                    title=sub.get("title", ""),
                    description=sub.get("description", ""),
                    subscribers=sub.get("subscribers", 0),
                    url=sub.get("url", ""),
                    is_nsfw=sub.get("is_nsfw", False),
                    reddit_created_utc=parse_created_utc(sub.get("created_utc")),
                    discovered_via_queries=queries_json,
                    discovery_count=1,
                    embedding_status="pending"
                )
                db.add(cache_entry)
                logger.debug(f"Cached new subreddit: {name}")

            cached_count += 1

        try:
            db.commit()
            logger.info(f"Successfully cached {cached_count} subreddits")
        except Exception as e:
            logger.error(f"Error committing subreddit cache: {e}")
            db.rollback()
            raise

        return cached_count

    def get_cached_subreddit(self, db: Session, name: str) -> Optional[SubredditCache]:
        """Get a single cached subreddit by name"""
        return db.query(SubredditCache).filter(
            SubredditCache.name == name
        ).first()

    def get_all_cached(
        self,
        db: Session,
        limit: int = 1000,
        offset: int = 0
    ) -> List[SubredditCache]:
        """Get all cached subreddits, ordered by discovery_count desc"""
        return db.query(SubredditCache).order_by(
            SubredditCache.discovery_count.desc(),
            SubredditCache.subscribers.desc()
        ).offset(offset).limit(limit).all()

    def get_pending_for_embedding(
        self,
        db: Session,
        limit: int = 100
    ) -> List[SubredditCache]:
        """Get subreddits pending vector embedding"""
        return db.query(SubredditCache).filter(
            SubredditCache.embedding_status == "pending"
        ).order_by(
            SubredditCache.discovery_count.desc()
        ).limit(limit).all()

    def get_cache_stats(self, db: Session) -> Dict[str, Any]:
        """Get cache statistics"""
        total = db.query(SubredditCache).count()
        pending_embedding = db.query(SubredditCache).filter(
            SubredditCache.embedding_status == "pending"
        ).count()

        return {
            "total_cached": total,
            "pending_embedding": pending_embedding,
            "embedded": total - pending_embedding
        }
