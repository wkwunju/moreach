import logging
from typing import Optional

from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class AudienceAnalyzer:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def analyze(self, profile: dict, posts: list[dict]) -> str:
        """
        Analyze the creator's audience and target demographic.
        
        Returns a concise analysis of:
        - Demographics (age range, gender distribution if identifiable)
        - Interests and values
        - Engagement patterns
        - Geographic distribution hints
        """
        profile_fields = {
            "fullName": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "businessCategoryName": profile.get("businessCategoryName", ""),
            "followersCount": profile.get("followersCount", 0),
            "hashtags": profile.get("hashtags", []),
        }
        
        # Extract post data for analysis
        post_data = []
        for post in posts[:10]:  # Analyze up to 10 recent posts
            post_data.append({
                "caption": post.get("caption", "")[:500],  # Truncate long captions
                "hashtags": post.get("hashtags", [])[:10],
                "mentions": post.get("mentions", [])[:5],
                "likesCount": post.get("likesCount", 0),
                "commentsCount": post.get("commentsCount", 0),
                "locationName": post.get("locationName", ""),
            })
        
        prompt = (
            "Analyze the target audience for this Instagram creator based on their profile and recent posts. "
            "Provide a concise 2-3 sentence analysis covering:\n"
            "1. Primary demographic (age range, lifestyle, interests)\n"
            "2. Audience values and motivations\n"
            "3. Geographic focus if evident\n\n"
            "Be specific and factual. If information is unclear, state that explicitly.\n\n"
            f"Profile: {profile_fields}\n"
            f"Recent posts: {post_data}\n"
        )
        
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You are an expert social media analyst specializing in audience demographics."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        
        analysis = _extract_content(response)
        logger.info("Audience analysis generated for profile")
        return analysis


def _extract_content(response: dict) -> str:
    if "text" in response:
        return response["text"].strip()
    if "choices" in response:
        return response["choices"][0]["message"]["content"].strip()
    candidates = response.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return ""
    return parts[0].get("text", "").strip()

