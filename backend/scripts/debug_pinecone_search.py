"""
Debug script to test Pinecone search functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.discovery.search import DiscoverySearch
from app.services.vector.pinecone import PineconeVectorStore

def main():
    print("=== Testing Pinecone Search ===\n")
    
    # Test 1: Check if vector store is accessible
    print("1. Initializing Pinecone Vector Store...")
    try:
        vector_store = PineconeVectorStore()
        print("   ✓ Pinecone initialized")
        print(f"   - Supports text records: {vector_store.supports_text_records()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Try a search
    print("\n2. Testing search...")
    description = "online glasses company"
    constraints = "influencer in germany less than 10k followers"
    
    try:
        search = DiscoverySearch()
        intent, embedding, matches = search.search(description, constraints, top_k=20)
        
        print(f"   ✓ Search completed")
        print(f"   - Intent: {intent}")
        print(f"   - Embedding size: {len(embedding) if embedding else 0}")
        print(f"   - Matches found: {len(matches)}")
        
        if matches:
            print("\n   Top 3 matches:")
            for i, match in enumerate(matches[:3], 1):
                handle = match.get("id") or match.get("metadata", {}).get("handle")
                score = match.get("score", 0)
                followers = match.get("metadata", {}).get("followers", 0)
                print(f"   {i}. @{handle} (score: {score:.3f}, followers: {followers})")
        else:
            print("\n   ⚠️ No matches found!")
            print("\n3. Checking Pinecone index stats...")
            try:
                # Try to get some stats from Pinecone
                if hasattr(vector_store.index, 'describe_index_stats'):
                    stats = vector_store.index.describe_index_stats()
                    print(f"   Index stats: {stats}")
            except Exception as e:
                print(f"   Could not get stats: {e}")
                
    except Exception as e:
        print(f"   ✗ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

