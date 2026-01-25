import logging
from typing import Any, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self.base_url = settings.openai_base_url
        self.api_key = settings.openai_api_key

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def chat(self, messages, model=None, temperature=0.2):
        logger.info("LLM chat request: provider=openai model=%s", model or settings.openai_model)
        payload = {
            "model": model or settings.openai_model,
            "messages": messages,
            "temperature": temperature,
        }
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def embed(self, texts, model=None):
        logger.info(
            "Embedding request: provider=openai model=%s items=%s",
            model or settings.openai_embedding_model,
            len(texts),
        )
        payload = {
            "model": model or settings.openai_embedding_model,
            "input": texts,
            "dimensions": settings.openai_embedding_dimensions,
        }
        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


class GeminiClient:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed. Run pip install -r requirements.txt") from exc
        self.client = genai.Client(api_key=self.api_key or None)

    def _messages_to_text(self, messages: list[dict]) -> str:
        parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            parts.append(f"{role.upper()}: {content}")
        return "\n".join(parts)

    def chat(self, messages, model=None, temperature=0.2) -> dict[str, Any]:
        model_name = model or settings.gemini_model
        logger.info("LLM chat request: provider=gemini model=%s", model_name)
        prompt = self._messages_to_text(messages)
        response = self.client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"temperature": temperature},
        )
        return {"text": response.text or ""}

    def embed(self, texts, model=None) -> dict[str, Any]:
        model_name = model or settings.gemini_embedding_model
        logger.info("Embedding request: provider=gemini model=%s items=%s", model_name, len(texts))
        response = self.client.models.embed_content(
            model=model_name,
            contents=texts,
        )
        embeddings = getattr(response, "embeddings", None)
        if embeddings is None:
            return {"embeddings": []}
        return {"embeddings": [{"values": emb.values} for emb in embeddings]}


from typing import Optional


def get_llm_client(provider: Optional[str] = None):
    selected = (provider or settings.llm_provider).lower()
    if selected == "gemini":
        return GeminiClient()
    return OpenAIClient()
