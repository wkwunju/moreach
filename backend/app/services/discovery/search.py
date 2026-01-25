import logging

from app.core.config import settings
from app.services.llm.intent import IntentParser
from app.services.llm.embeddings import EmbeddingService
from app.services.vector.pinecone import PineconeVectorStore


logger = logging.getLogger(__name__)


class DiscoverySearch:
    def __init__(self):
        # 根据配置选择 IntentParser 实现
        if settings.use_langchain_chains:
            from app.services.langchain.chains.intent_chain import IntentChainService
            self.intent_parser = IntentChainService()
            logger.info("Using LangChain IntentChainService")
        else:
            self.intent_parser = IntentParser()
            logger.info("Using legacy IntentParser")
        
        self.embedding_service = EmbeddingService()
        self.vector_store = PineconeVectorStore()

    def search(self, description: str, constraints: str, top_k: int) -> tuple[str, list[float], list[dict]]:
        intent = self.intent_parser.parse(description, constraints)
        logger.info("Intent parsed: %s", intent)
        if settings.embedding_provider.lower() == "pinecone":
            if not self.vector_store.supports_text_records():
                raise RuntimeError(
                    "Pinecone index-integrated embedding requires the newer pinecone SDK "
                    "with upsert_records/search support. Upgrade pinecone or set EMBEDDING_PROVIDER=openai."
                )
            embedding = []
            matches = self.vector_store.search_text(intent, top_k)
        else:
            embedding = self.embedding_service.embed_query(intent)
            matches = self.vector_store.query(embedding, top_k)
        logger.info("Vector search returned %s matches", len(matches))
        return intent, embedding, matches
