"""
Test script to verify subreddit scoring functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.reddit.discovery import RedditDiscoveryService

def test_subreddit_scoring():
    """Test the complete subreddit discovery and scoring flow"""
    
    business_description = "I help SaaS startups with digital marketing and growth strategies"
    
    print("=" * 80)
    print("Testing Subreddit Discovery & Scoring")
    print("=" * 80)
    print(f"\nBusiness: {business_description}\n")
    
    discovery_service = RedditDiscoveryService()
    
    # Step 1: Generate search queries
    print("Step 1: Generating search queries...")
    search_queries = discovery_service.generate_search_queries(business_description)
    print(f"Generated {len(search_queries)} queries:")
    for i, query in enumerate(search_queries, 1):
        print(f"  {i}. {query}")
    
    # Step 2: Discover subreddits
    print(f"\nStep 2: Discovering subreddits...")
    subreddits = discovery_service.discover_subreddits(search_queries, limit_per_query=10)
    print(f"Found {len(subreddits)} unique subreddits")
    
    # Step 3: Rank subreddits
    print(f"\nStep 3: Ranking subreddits by relevance...")
    ranked_subreddits = discovery_service.rank_subreddits(subreddits, business_description)
    
    # Display results
    print("\n" + "=" * 80)
    print("TOP 10 SUBREDDITS (by relevance)")
    print("=" * 80)
    print(f"{'Rank':<6} {'Subreddit':<25} {'Subscribers':<12} {'Relevance':<10} {'Composite':<10}")
    print("-" * 80)
    
    for i, sub in enumerate(ranked_subreddits[:10], 1):
        print(f"{i:<6} r/{sub['name']:<24} {sub['subscribers']:>11,} {sub.get('relevance_score', 0):<10.2f} {sub.get('composite_score', 0):<10.2f}")
    
    print("\n" + "=" * 80)
    print("DETAILED INFO (Top 3)")
    print("=" * 80)
    
    for i, sub in enumerate(ranked_subreddits[:3], 1):
        print(f"\n{i}. r/{sub['name']}")
        print(f"   Title: {sub['title']}")
        print(f"   Subscribers: {sub['subscribers']:,}")
        print(f"   Relevance Score: {sub.get('relevance_score', 0):.2f}")
        print(f"   Composite Score: {sub.get('composite_score', 0):.2f}")
        print(f"   Description: {sub['description'][:150]}...")
    
    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_subreddit_scoring()

