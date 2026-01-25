from pinecone import Pinecone
import logging

from app.core.config import settings
from app.services.vector.client import VectorStore


logger = logging.getLogger(__name__)


class PineconeVectorStore(VectorStore):
    def __init__(self):
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        if settings.pinecone_host:
            self.index = self.client.Index(host=settings.pinecone_host)
        else:
            self.index = self.client.Index(settings.pinecone_index)

    def supports_text_records(self) -> bool:
        return hasattr(self.index, "upsert_records") and hasattr(self.index, "search")

    def upsert(self, vectors: list[dict]) -> None:
        if not vectors:
            return
        self.index.upsert(vectors=vectors)

    def upsert_texts(self, records: list[dict]) -> None:
        if not records:
            return
        if not self.supports_text_records():
            raise RuntimeError("Pinecone client does not support upsert_records.")
        namespace = settings.pinecone_namespace or "__default__"
        
        # Pinecone upsert_records with inference API expects records without metadata in the record itself
        # Metadata should be at the top level alongside id and text
        cleaned_records = []
        for record in records:
            cleaned_record = {
                "id": str(record["id"]),
                "text": str(record["text"]),
            }
            
            # Add metadata fields directly at the top level, not nested under "metadata"
            if "metadata" in record and record["metadata"]:
                MAX_METADATA_STRING_LENGTH = 10000  # Pinecone's metadata limit per field
                for key, value in record["metadata"].items():
                    if value is None:
                        continue
                    elif isinstance(value, str):
                        # Truncate strings that are too long
                        cleaned_record[key] = value[:MAX_METADATA_STRING_LENGTH] if len(value) > MAX_METADATA_STRING_LENGTH else value
                    elif isinstance(value, (int, float, bool)):
                        cleaned_record[key] = value
                    elif isinstance(value, list):
                        # Only allow list of strings
                        cleaned_record[key] = [str(v)[:MAX_METADATA_STRING_LENGTH] if len(str(v)) > MAX_METADATA_STRING_LENGTH else str(v) for v in value if v is not None]
                    else:
                        # Convert other types to string and truncate if needed
                        str_value = str(value)
                        cleaned_record[key] = str_value[:MAX_METADATA_STRING_LENGTH] if len(str_value) > MAX_METADATA_STRING_LENGTH else str_value
            
            cleaned_records.append(cleaned_record)
        
        # Debug: log the first record to see what we're sending
        if cleaned_records:
            logger.info("Sample upsert_records record: %s", cleaned_records[0])
        
        self.index.upsert_records(namespace=namespace, records=cleaned_records)

    def query(self, vector: list[float], top_k: int) -> list[dict]:
        response = self.index.query(vector=vector, top_k=top_k, include_metadata=True)
        return _normalize_matches(response)

    def search_text(self, text: str, top_k: int) -> list[dict]:
        if not self.supports_text_records():
            raise RuntimeError("Pinecone client does not support search with text inputs.")
        namespace = settings.pinecone_namespace or "__default__"
        response = self.index.search(namespace=namespace, query={"inputs": {"text": text}, "top_k": top_k})
        return _normalize_matches(response)


def _normalize_matches(response) -> list[dict]:
    """
    Normalize Pinecone response to a consistent list of matches.
    Handles both query() and search() API responses.
    """
    if hasattr(response, "to_dict"):
        response = response.to_dict()
    elif hasattr(response, "model_dump"):
        response = response.model_dump()
    
    if not isinstance(response, dict):
        return []
    
    # Handle search() API response: {"result": {"hits": [...]}}
    if "result" in response and isinstance(response["result"], dict):
        hits = response["result"].get("hits", [])
        if hits:
            # Convert search() format to query() format for consistency
            normalized = []
            for hit in hits:
                # Get metadata from fields, but also check top-level and _metadata
                metadata = {}
                
                # First try 'fields' (most common for search API)
                if "fields" in hit and isinstance(hit["fields"], dict):
                    metadata.update(hit["fields"])
                
                # Also check '_metadata' key
                if "_metadata" in hit and isinstance(hit["_metadata"], dict):
                    metadata.update(hit["_metadata"])
                
                # Also check 'metadata' key (for backward compatibility)
                if "metadata" in hit and isinstance(hit["metadata"], dict):
                    metadata.update(hit["metadata"])
                
                # Some fields might be at top level (excluding known system fields)
                system_fields = {"_id", "_score", "id", "score", "fields", "metadata", "_metadata", "text"}
                for key, value in hit.items():
                    if key not in system_fields and key not in metadata:
                        metadata[key] = value
                
                normalized.append({
                    "id": hit.get("_id", hit.get("id", "")),
                    "score": hit.get("_score", hit.get("score", 0.0)),
                    "metadata": metadata,
                })
            return normalized
    
    # Handle query() API response: {"matches": [...]}
    if "matches" in response:
        return response["matches"]
    
    # Handle alternative formats
    if "results" in response:
        return response["results"]
    
    return []
