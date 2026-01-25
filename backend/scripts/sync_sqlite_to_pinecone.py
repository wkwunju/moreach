"""
Script to sync SQLite data to Pinecone
Ensures Pinecone index matches SQLite (single source of truth)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import SessionLocal
from app.models.tables import Influencer
from app.services.discovery.pipeline import DiscoveryPipeline, DiscoveryCandidate

def main():
    print("=== Syncing SQLite → Pinecone ===\n")
    
    db = SessionLocal()
    
    # 1. Get all influencers from SQLite (source of truth)
    print("1. Fetching influencers from SQLite...")
    influencers = db.query(Influencer).all()
    print(f"   Found {len(influencers)} influencers in SQLite\n")
    
    if not influencers:
        print("   No influencers to sync!")
        return
    
    # 2. Convert to candidates
    print("2. Converting to candidates...")
    candidates = []
    for inf in influencers:
        candidate = DiscoveryCandidate(
            handle=inf.handle,
            name=inf.name or "",
            bio=inf.bio or "",
            profile_summary=inf.profile_summary or "",
            profile_url=inf.profile_url or f"https://instagram.com/{inf.handle}",
            followers=float(inf.followers or 0),
            avg_likes=float(inf.avg_likes or 0),
            avg_comments=float(inf.avg_comments or 0),
            avg_video_views=float(inf.avg_video_views or 0),
            highest_likes=float(inf.highest_likes or 0),
            highest_comments=float(inf.highest_comments or 0),
            highest_video_views=float(inf.highest_video_views or 0),
            post_sharing_percentage=float(inf.post_sharing_percentage or 0),
            post_collaboration_percentage=float(inf.post_collaboration_percentage or 0),
            audience_analysis=inf.audience_analysis or "",
            collaboration_opportunity=inf.collaboration_opportunity or "",
            email=inf.email or "",
            external_url=inf.external_url or "",
            category=inf.category or "",
            tags=inf.tags or "",
            country=inf.country or "",
            gender=inf.gender or "",
        )
        candidates.append(candidate)
    
    print(f"   Converted {len(candidates)} candidates\n")
    
    # 3. Upsert to Pinecone
    print("3. Upserting to Pinecone...")
    pipeline = DiscoveryPipeline()
    try:
        pipeline._upsert_vectors(candidates)
        print(f"   ✅ Successfully synced {len(candidates)} influencers to Pinecone\n")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Show summary
    print("4. Summary:")
    print(f"   - Total synced: {len(candidates)}")
    
    # Check data quality
    with_summary = sum(1 for c in candidates if c.profile_summary)
    with_audience = sum(1 for c in candidates if c.audience_analysis)
    with_collaboration = sum(1 for c in candidates if c.collaboration_opportunity)
    
    print(f"   - With profile_summary: {with_summary} ({with_summary/len(candidates)*100:.1f}%)")
    print(f"   - With audience_analysis: {with_audience} ({with_audience/len(candidates)*100:.1f}%)")
    print(f"   - With collaboration_opportunity: {with_collaboration} ({with_collaboration/len(candidates)*100:.1f}%)")
    
    print("\n✅ Sync complete! SQLite and Pinecone are now consistent.")

if __name__ == "__main__":
    main()

