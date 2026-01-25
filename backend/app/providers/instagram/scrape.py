from typing import Optional
import logging

from app.core.config import settings
from app.providers.apify.client import ApifyClient
from app.providers.base import InstagramScrapeProvider


logger = logging.getLogger(__name__)


class ApifyInstagramProvider(InstagramScrapeProvider):
    def __init__(self, client: Optional[ApifyClient] = None):
        self.client = client or ApifyClient()

    def profile(self, handle: str) -> dict:
        """
        Fetch Instagram profile data with recent posts.
        
        Uses resultsType: "details" to get comprehensive profile information
        including latestPosts, latestIgtvVideos, etc.
        """
        profile_url = f"https://www.instagram.com/{handle}/"
        
        run_input = {
            "directUrls": [profile_url],
            "resultsType": "details",  # Get detailed profile info including posts
            "resultsLimit": 1,
            "addParentData": False,
            "searchType": "hashtag",
            "searchLimit": 1,
        }
        
        try:
            items = self.client.run_actor(settings.apify_instagram_actor, run_input)
            if not items:
                logger.warning("No profile data returned for handle: %s", handle)
                return {}
            
            profile_data = items[0]
            followers = profile_data.get("followersCount", 0)
            posts_count = profile_data.get("postsCount", 0)
            
            logger.info(
                "Profile fetched for %s: %s followers, %s posts", 
                handle, 
                followers,
                posts_count
            )
            return profile_data
            
        except Exception as e:
            logger.error("Failed to fetch profile for %s: %s", handle, e, exc_info=True)
            return {}

    def recent_posts(self, handle: str, limit: int) -> list[dict]:
        """
        Fetch recent posts from Instagram profile.
        
        Note: When calling profile() with resultsType="details", 
        the response includes "latestPosts" array. This method is kept for compatibility
        but you should prefer using profile()["latestPosts"] for better efficiency.
        """
        profile_url = f"https://www.instagram.com/{handle}/"
        
        run_input = {
            "directUrls": [profile_url],
            "resultsType": "posts",  # Get posts from the profile
            "resultsLimit": limit,
            "addParentData": False,
        }
        
        try:
            items = self.client.run_actor(settings.apify_instagram_actor, run_input)
            posts = items[:limit] if items else []
            logger.info("Fetched %s posts for %s", len(posts), handle)
            return posts
            
        except Exception as e:
            logger.error("Failed to fetch posts for %s: %s", handle, e, exc_info=True)
            return []
