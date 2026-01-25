import logging
from typing import Optional

from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class ProfileSummaryGenerator:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def generate(self, profile: dict, posts: list[dict]) -> str:
        profile_fields = {
            "fullName": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "businessCategoryName": profile.get("businessCategoryName", ""),
            "hashtags": profile.get("hashtags", []),
            "followersCount": profile.get("followersCount", 0),
        }
        captions = [post.get("caption", "") for post in posts if post]
        prompt = (
            "Summarize this Instagram creator in 1-2 sentences. "
            "Focus on lifestyle, interests, location hints, and audience tone. "
            "If data is missing, make no assumptions. Keep it factual.\n\n"
            f"Profile: {profile_fields}\n"
            f"Recent captions: {captions[:8]}\n"
        )
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You write concise, neutral creator summaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        summary = _extract_content(response)
        logger.info("Profile summary generated")
        return summary


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
