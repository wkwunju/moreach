"""
Debug script to inspect the actual Pinecone search response structure
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.vector.pinecone import PineconeVectorStore
from app.core.config import settings

def main():
    print("=== Pinecone Response Structure Inspector ===\n")
    
    # Initialize Pinecone
    print("1. Initializing Pinecone...")
    vector_store = PineconeVectorStore()
    print(f"   ✓ Connected to index")
    print(f"   - Supports text records: {vector_store.supports_text_records()}\n")
    
    # Test search with a simple query
    print("2. Running test search...")
    test_query = "german fashion model influencer"
    
    try:
        # Get raw response
        namespace = settings.pinecone_namespace or "__default__"
        raw_response = vector_store.index.search(
            text=test_query,
            top_k=3,
            namespace=namespace
        )
        
        print(f"   ✓ Search completed\n")
        
        # Print raw response structure
        print("3. Raw Response Structure:")
        print("=" * 60)
        if hasattr(raw_response, "to_dict"):
            response_dict = raw_response.to_dict()
        elif hasattr(raw_response, "model_dump"):
            response_dict = raw_response.model_dump()
        else:
            response_dict = raw_response
            
        print(json.dumps(response_dict, indent=2, default=str))
        print("=" * 60)
        print()
        
        # Analyze structure
        print("4. Structure Analysis:")
        if isinstance(response_dict, dict):
            print(f"   Top-level keys: {list(response_dict.keys())}")
            
            if "result" in response_dict:
                result = response_dict["result"]
                if isinstance(result, dict):
                    print(f"   Result keys: {list(result.keys())}")
                    
                    if "hits" in result and result["hits"]:
                        hit = result["hits"][0]
                        print(f"\n   First hit structure:")
                        print(f"   - Hit keys: {list(hit.keys())}")
                        
                        if "fields" in hit:
                            fields = hit["fields"]
                            print(f"   - Fields keys: {list(fields.keys())}")
                            print(f"\n   Sample field values:")
                            for key in ["handle", "name", "followers", "bio", "profile_summary", "audience_analysis"][:5]:
                                if key in fields:
                                    value = fields[key]
                                    if isinstance(value, str) and len(value) > 100:
                                        value = value[:100] + "..."
                                    print(f"     {key}: {value}")
                        
                        # Check if metadata is elsewhere
                        if "_metadata" in hit:
                            print(f"   - Found _metadata key with: {list(hit['_metadata'].keys())}")
                        if "metadata" in hit:
                            print(f"   - Found metadata key with: {list(hit['metadata'].keys())}")
                            
            elif "matches" in response_dict:
                matches = response_dict["matches"]
                if matches:
                    match = matches[0]
                    print(f"\n   First match structure:")
                    print(f"   - Match keys: {list(match.keys())}")
                    if "metadata" in match:
                        print(f"   - Metadata keys: {list(match['metadata'].keys())}")
        
        print("\n5. Testing _normalize_matches function:")
        from app.services.vector.pinecone import _normalize_matches
        normalized = _normalize_matches(raw_response)
        print(f"   ✓ Normalized {len(normalized)} matches")
        
        if normalized:
            first = normalized[0]
            print(f"\n   First normalized match:")
            print(f"   - Keys: {list(first.keys())}")
            print(f"   - ID: {first.get('id')}")
            print(f"   - Score: {first.get('score')}")
            if "metadata" in first:
                meta = first["metadata"]
                print(f"   - Metadata keys: {list(meta.keys())}")
                print(f"   - Metadata sample:")
                for key in ["handle", "name", "followers", "bio", "profile_summary"][:5]:
                    if key in meta:
                        value = meta[key]
                        if isinstance(value, str) and len(value) > 80:
                            value = value[:80] + "..."
                        print(f"     {key}: {value}")
                    else:
                        print(f"     {key}: <NOT FOUND>")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
