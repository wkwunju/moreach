import json
import logging

from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class ProfileAttributeExtractor:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def extract(self, profile: dict, posts: list[dict]) -> dict:
        profile_fields = {
            "fullName": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "businessCategoryName": profile.get("businessCategoryName", ""),
            "externalUrl": profile.get("externalUrl", ""),
        }
        captions = [post.get("caption", "") for post in posts if post]
        prompt = (
            "From the creator profile and recent captions, extract structured attributes. "
            "If not explicitly stated, return empty string for that field.\n"
            "Return JSON ONLY with keys: country, gender.\n\n"
            f"Profile: {profile_fields}\n"
            f"Recent captions: {captions[:8]}\n"
        )
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You extract structured metadata without guessing."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        content = _extract_content(response)
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Attribute extractor returned invalid JSON: %s", content)
            return {"country": "", "gender": ""}
        return {
            "country": parsed.get("country", "") or "",
            "gender": parsed.get("gender", "") or "",
        }


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
