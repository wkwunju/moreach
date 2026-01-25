"""
Reddit API Client using PRAW
Handles rate limiting (100 requests/minute on free tier)
"""
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import praw
from praw.models import Subreddit, Submission, Comment

from app.core.config import settings


logger = logging.getLogger(__name__)


class RedditClient:
    """
    Reddit API client with rate limiting
    Free tier: 100 requests/minute
    """
    
    def __init__(self):
        self.client = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        
        # Rate limiting: 100 requests/minute = 1 request per 0.6 seconds
        self.min_request_interval = 0.6
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def search_subreddits(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for subreddits by query
        Returns list of subreddit metadata
        """
        self._rate_limit()
        logger.info(f"Searching subreddits for: {query}")
        
        results = []
        try:
            subreddits = self.client.subreddits.search(query, limit=limit)
            for subreddit in subreddits:
                self._rate_limit()
                results.append({
                    "name": subreddit.display_name,
                    "title": subreddit.title,
                    "description": subreddit.public_description or "",
                    "subscribers": subreddit.subscribers or 0,
                    "url": f"https://reddit.com/r/{subreddit.display_name}",
                    "is_nsfw": subreddit.over18,
                })
        except Exception as e:
            logger.error(f"Error searching subreddits: {e}")
        
        return results
    
    def get_subreddit_info(self, subreddit_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a subreddit"""
        self._rate_limit()
        try:
            subreddit = self.client.subreddit(subreddit_name)
            return {
                "name": subreddit.display_name,
                "title": subreddit.title,
                "description": subreddit.public_description or "",
                "full_description": subreddit.description or "",
                "subscribers": subreddit.subscribers or 0,
                "url": f"https://reddit.com/r/{subreddit.display_name}",
                "is_nsfw": subreddit.over18,
                "created_utc": subreddit.created_utc,
            }
        except Exception as e:
            logger.error(f"Error getting subreddit info for r/{subreddit_name}: {e}")
            return None
    
    def get_new_posts(
        self, 
        subreddit_name: str, 
        limit: int = 100,
        since_timestamp: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get new posts from a subreddit
        
        Args:
            subreddit_name: Name of subreddit
            limit: Max number of posts (default 100)
            since_timestamp: Only return posts after this timestamp
        """
        self._rate_limit()
        logger.info(f"Fetching new posts from r/{subreddit_name}")
        
        posts = []
        try:
            subreddit = self.client.subreddit(subreddit_name)
            
            for submission in subreddit.new(limit=limit):
                # Skip if older than since_timestamp
                if since_timestamp and submission.created_utc < since_timestamp:
                    continue
                
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext or "",
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": subreddit_name,
                    "link_flair_text": submission.link_flair_text or "",
                })
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
        
        logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
        return posts
    
    def get_hot_posts(
        self, 
        subreddit_name: str, 
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Get hot/trending posts from a subreddit"""
        self._rate_limit()
        logger.info(f"Fetching hot posts from r/{subreddit_name}")
        
        posts = []
        try:
            subreddit = self.client.subreddit(subreddit_name)
            
            for submission in subreddit.hot(limit=limit):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext or "",
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": subreddit_name,
                    "link_flair_text": submission.link_flair_text or "",
                })
        except Exception as e:
            logger.error(f"Error fetching hot posts from r/{subreddit_name}: {e}")
        
        return posts
    
    def get_post_details(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post"""
        self._rate_limit()
        try:
            submission = self.client.submission(id=post_id)
            return {
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext or "",
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": submission.subreddit.display_name,
                "link_flair_text": submission.link_flair_text or "",
            }
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            return None

