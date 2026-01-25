import logging
from typing import Optional

from app.core.config import settings
from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class GoogleDorkGenerator:
    def __init__(self, client=None):
        self.client = client or get_llm_client(settings.dork_provider)

    def generate(self, description: str, constraints: str) -> str:
        prompt = (
            "Generate ONE optimized Google search query for Instagram influencer discovery. "
            "Your job is to turn the user's intent into a WORKING dork that returns results.\n"
            "Follow these rules strictly:\n"
            "1. Start with site:instagram.com/*/ to target profile headers.\n"
            "2. If the niche is a product category (e.g., eyewear), avoid the literal product word and instead use "
            "adjacent lifestyle/interest terms. Do NOT just echo the input words.\n"
            "3. Geography handling:\n"
            "   - If a specific country is given, include that country and its top 5 most populous cities (grouped).\n"
            "   - If a region is given (e.g., Western Europe), expand it into representative countries and major cities "
            "across that region. Do NOT include the raw region term if it is too broad to yield results.\n"
            "   - If geography is missing, omit geography entirely.\n"
            "4. Follower range: include ONLY if explicitly specified.\n"
            "4a. When a follower range is specified, express it as a numeric range phrase like "
            "\"1000..10000 followers\". Do NOT use shorthand like 10k/20k.\n"
            "5. Contact footprint: include ONLY if explicitly requested; otherwise omit it.\n"
            "6. Exclude post/media pages: -inurl:\"/p/\" -inurl:\"/reel/\" -inurl:\"/reels/\" -inurl:\"/tv/\".\n"
            "7. Use parentheses for every OR group, and avoid mixing OR/AND without grouping.\n"
            "8. Output ONLY the raw search string. No explanations.\n\n"
            f"Description: {description}\n"
            f"Constraints: {constraints}\n"
        )
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You are a growth hacking and Google dorking expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        query = _extract_content(response)
        logger.info("Generated Google dork query: %s", query)
        return query


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
