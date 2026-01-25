import logging
from typing import Optional

from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class CollaborationAnalyzer:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def analyze(self, profile: dict, posts: list[dict], business_description: str = "") -> str:
        """
        Analyze collaboration opportunities with this creator.
        
        Returns a concise analysis of:
        - Brand fit and alignment
        - Content integration opportunities
        - Potential collaboration formats
        - Estimated engagement value
        """
        profile_fields = {
            "handle": profile.get("username", ""),
            "fullName": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "businessCategoryName": profile.get("businessCategoryName", ""),
            "followersCount": profile.get("followersCount", 0),
        }
        
        # Extract collaboration indicators from posts
        collaboration_data = {
            "has_brand_mentions": False,
            "sponsored_posts": 0,
            "product_showcases": 0,
            "common_hashtags": [],
        }
        
        for post in posts[:10]:
            caption = post.get("caption", "").lower()
            mentions = post.get("mentions", [])
            hashtags = post.get("hashtags", [])
            
            # Detect sponsored content
            if any(keyword in caption for keyword in ["#ad", "#sponsored", "#partner", "partnership"]):
                collaboration_data["sponsored_posts"] += 1
            
            if mentions:
                collaboration_data["has_brand_mentions"] = True
            
            collaboration_data["common_hashtags"].extend(hashtags[:5])
        
        prompt = (
            "Analyze collaboration opportunities with this Instagram creator. "
            "Provide a concise 2-3 sentence assessment covering:\n"
            "1. Brand partnership experience (based on sponsored content indicators)\n"
            "2. Content style and collaboration formats they excel at\n"
            "3. Unique value proposition for brand partnerships\n\n"
            f"Profile: {profile_fields}\n"
            f"Collaboration indicators: {collaboration_data}\n"
        )
        
        if business_description:
            prompt += f"\nBusiness context: {business_description}\n"
        
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You are an influencer marketing strategist analyzing collaboration potential."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        
        analysis = _extract_content(response)
        logger.info("Collaboration analysis generated for profile")
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

