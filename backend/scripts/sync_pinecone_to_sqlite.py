"""
Sync data from Pinecone to SQLite (ONE-TIME FIX)
Use this when Pinecone has newer data than SQLite

This is a one-time fix script. After running this, the normal flow should keep them in sync.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import SessionLocal
from app.models.tables import Influencer
from app.services.vector.pinecone import PineconeVectorStore
from app.core.config import settings

def sync_from_pinecone():
    """
    Sync influencer data from Pinecone to SQLite.
    Updates SQLite records with Pinecone metadata (which is newer).
    """
    print("=== Syncing Pinecone → SQLite (Data Fix) ===\n")
    print("⚠️  This will update SQLite with Pinecone metadata")
    print("    Use this when Pinecone has newer data than SQLite\n")
    
    db = SessionLocal()
    vector_store = PineconeVectorStore()
    
    # Get all influencers from SQLite
    print("1. Fetching all influencers from SQLite...")
    influencers = db.query(Influencer).all()
    print(f"   Found {len(influencers)} influencers in SQLite\n")
    
    if not influencers:
        print("   No influencers to sync!")
        return
    
    # For each influencer, fetch from Pinecone and update SQLite
    print("2. Fetching data from Pinecone and updating SQLite...\n")
    
    updated_count = 0
    not_found_count = 0
    error_count = 0
    
    for influencer in influencers:
        handle = influencer.handle
        print(f"   Processing @{handle}...")
        
        try:
            # Search Pinecone for this handle
            # Use the handle as query to find exact match
            matches = vector_store.search_text(handle, top_k=5)
            
            # Find exact match by handle
            match = None
            for m in matches:
                if m.get("id") == handle:
                    match = m
                    break
            
            if not match:
                print(f"      ⚠️  Not found in Pinecone")
                not_found_count += 1
                continue
            
            # Get metadata from Pinecone
            meta = match.get("metadata", {})
            
            if not meta:
                print(f"      ⚠️  No metadata in Pinecone")
                not_found_count += 1
                continue
            
            # Update SQLite with Pinecone data
            updated_fields = []
            
            # Text fields
            text_fields = {
                "name": meta.get("name", ""),
                "bio": meta.get("bio", ""),
                "profile_summary": meta.get("profile_summary", ""),
                "category": meta.get("category", ""),
                "tags": meta.get("tags", ""),
                "audience_analysis": meta.get("audience_analysis", ""),
                "collaboration_opportunity": meta.get("collaboration_opportunity", ""),
                "email": meta.get("email", ""),
                "external_url": meta.get("external_url", ""),
                "country": meta.get("country", ""),
                "gender": meta.get("gender", ""),
            }
            
            for field, new_value in text_fields.items():
                if new_value:  # Pinecone has value
                    current_value = getattr(influencer, field, "")
                    if not current_value or current_value != new_value:
                        setattr(influencer, field, new_value)
                        updated_fields.append(field)
            
            # Numeric fields
            numeric_fields = {
                "followers": meta.get("followers", 0),
                "avg_likes": meta.get("avg_likes", 0),
                "avg_comments": meta.get("avg_comments", 0),
                "avg_video_views": meta.get("avg_video_views", 0),
                "highest_likes": meta.get("highest_likes", 0),
                "highest_comments": meta.get("highest_comments", 0),
                "highest_video_views": meta.get("highest_video_views", 0),
                "post_sharing_percentage": meta.get("post_sharing_percentage", 0),
                "post_collaboration_percentage": meta.get("post_collaboration_percentage", 0),
            }
            
            for field, new_value in numeric_fields.items():
                new_value = float(new_value) if new_value else 0.0
                current_value = float(getattr(influencer, field, 0))
                if new_value > 0 and new_value != current_value:
                    setattr(influencer, field, new_value)
                    updated_fields.append(field)
            
            if updated_fields:
                db.commit()
                print(f"      ✅ Updated: {', '.join(updated_fields[:5])}")
                if len(updated_fields) > 5:
                    print(f"         + {len(updated_fields) - 5} more fields")
                updated_count += 1
            else:
                print(f"      → No changes needed")
        
        except Exception as e:
            print(f"      ✗ Error: {e}")
            error_count += 1
            continue
    
    print(f"\n3. Summary:")
    print(f"   ✅ Updated: {updated_count} influencers")
    print(f"   → Unchanged: {len(influencers) - updated_count - not_found_count - error_count}")
    print(f"   ⚠️  Not found in Pinecone: {not_found_count}")
    print(f"   ✗ Errors: {error_count}")
    
    print("\n✅ Sync complete!")
    print("   SQLite now has the latest data from Pinecone")
    
    db.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Sync influencer data from Pinecone to SQLite (one-time fix)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Use this script when:
  - Pinecone has newer data than SQLite
  - You need to update existing SQLite records with Pinecone metadata

This is a ONE-TIME fix. After running this, the normal Pipeline flow
will keep both databases in sync.

Example:
  python scripts/sync_pinecone_to_sqlite.py
        """
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("\n⚠️  WARNING: This will update SQLite with Pinecone metadata")
        print("   Make sure you have a backup of your database!")
        response = input("\nContinue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cancelled.")
            return
        print()
    
    sync_from_pinecone()

if __name__ == "__main__":
    main()

