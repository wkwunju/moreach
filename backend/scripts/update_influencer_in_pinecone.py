"""
Update a single influencer in Pinecone after SQLite update
Usage: python scripts/update_influencer_in_pinecone.py <handle>
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import SessionLocal
from app.models.tables import Influencer
from app.services.discovery.pipeline import DiscoveryPipeline, DiscoveryCandidate

def update_influencer(handle: str):
    """
    Update a single influencer in Pinecone from SQLite data.
    Uses upsert which will replace existing record or create new one.
    """
    print(f"=== Updating @{handle} in Pinecone ===\n")
    
    db = SessionLocal()
    
    # 1. Get from SQLite (source of truth)
    print(f"1. Fetching @{handle} from SQLite...")
    influencer = db.query(Influencer).filter_by(handle=handle).first()
    
    if not influencer:
        print(f"   ✗ Influencer @{handle} not found in SQLite")
        print(f"   Make sure the handle exists in database first.")
        return False
    
    print(f"   ✓ Found @{handle} in SQLite")
    print(f"     Name: {influencer.name or 'N/A'}")
    print(f"     Followers: {influencer.followers:,.0f}")
    print(f"     Profile Summary: {len(influencer.profile_summary or '')} chars")
    print()
    
    # 2. Convert to candidate
    print(f"2. Converting to candidate...")
    candidate = DiscoveryCandidate(
        handle=influencer.handle,
        name=influencer.name or "",
        bio=influencer.bio or "",
        profile_summary=influencer.profile_summary or "",
        profile_url=influencer.profile_url or f"https://instagram.com/{handle}",
        followers=float(influencer.followers or 0),
        avg_likes=float(influencer.avg_likes or 0),
        avg_comments=float(influencer.avg_comments or 0),
        avg_video_views=float(influencer.avg_video_views or 0),
        highest_likes=float(influencer.highest_likes or 0),
        highest_comments=float(influencer.highest_comments or 0),
        highest_video_views=float(influencer.highest_video_views or 0),
        post_sharing_percentage=float(influencer.post_sharing_percentage or 0),
        post_collaboration_percentage=float(influencer.post_collaboration_percentage or 0),
        audience_analysis=influencer.audience_analysis or "",
        collaboration_opportunity=influencer.collaboration_opportunity or "",
        email=influencer.email or "",
        external_url=influencer.external_url or "",
        category=influencer.category or "",
        tags=influencer.tags or "",
        country=influencer.country or "",
        gender=influencer.gender or "",
    )
    print(f"   ✓ Candidate created")
    print()
    
    # 3. Upsert to Pinecone (will replace if exists)
    print(f"3. Upserting to Pinecone...")
    print(f"   This will replace existing record if it exists")
    
    try:
        pipeline = DiscoveryPipeline()
        pipeline._upsert_vectors([candidate])
        print(f"   ✓ Successfully upserted to Pinecone")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Verify
    print(f"4. Summary:")
    print(f"   ✓ @{handle} is now synced between SQLite and Pinecone")
    print(f"   ✓ Vector and metadata have been updated")
    print()
    
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Update influencer in Pinecone from SQLite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/update_influencer_in_pinecone.py charlenehoegger
  python scripts/update_influencer_in_pinecone.py fitness_mike

Notes:
  - The influencer must exist in SQLite first
  - This uses 'upsert' which replaces existing Pinecone records
  - Vector embedding will be regenerated from current SQLite data
        """
    )
    parser.add_argument("handle", help="Influencer handle (without @ symbol)")
    
    args = parser.parse_args()
    
    success = update_influencer(args.handle)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

