import logging
from typing import Optional

from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class IntentParser:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def parse(self, description: str, constraints: str) -> str:
        prompt = (
            "Extract a concise influencer discovery intent from the business description and constraints. "
            "Return a short plain-text query phrase." 
            f"\nDescription: {description}\nConstraints: {constraints}"
        )
        response = self.client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful intent extraction assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        content = _extract_content(response)
        logger.info("LLM intent raw output: %s", content)
        return content


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
