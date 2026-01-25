from typing import Optional

from app.core.config import settings
from app.services.llm.client import get_llm_client


class EmbeddingService:
    def __init__(self, client=None):
        self.client = client or get_llm_client()

    def embed_query(self, text: str) -> list[float]:
        if settings.embedding_provider.lower() == "pinecone":
            raise RuntimeError("Pinecone embedding is handled via index-integrated text search.")
        response = self.client.embed([text])
        return _extract_embedding(response, index=0)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if settings.embedding_provider.lower() == "pinecone":
            raise RuntimeError("Pinecone embedding is handled via index-integrated text upsert.")
        response = self.client.embed(texts)
        return _extract_embeddings(response)


def _extract_embedding(response: dict, index: int) -> list[float]:
    if "data" in response:
        item = response["data"][index]
        return item.get("embedding") or item.get("values") or []
    embeddings = response.get("embeddings", [])
    if embeddings:
        return embeddings[index].get("values", [])
    vectors = response.get("vectors", [])
    if vectors:
        return vectors[index].get("values", [])
    return response.get("embedding", {}).get("values", [])


def _extract_embeddings(response: dict) -> list[list[float]]:
    if "data" in response:
        return [item.get("embedding") or item.get("values") or [] for item in response["data"]]
    embeddings = response.get("embeddings", [])
    if embeddings:
        return [item.get("values", []) for item in embeddings]
    vectors = response.get("vectors", [])
    return [item.get("values", []) for item in vectors]
