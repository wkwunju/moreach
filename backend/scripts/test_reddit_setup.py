"""
Test script to verify Reddit API setup

Usage:
    python scripts/test_reddit_setup.py
"""
import sys
sys.path.insert(0, ".")

from app.providers.reddit.client import RedditClient
from app.services.reddit.discovery import RedditDiscoveryService
from app.core.config import settings


def test_reddit_credentials():
    """Test if Reddit API credentials are configured"""
    print("🔍 Checking Reddit API credentials...")
    
    if not settings.reddit_client_id:
        print("❌ REDDIT_CLIENT_ID not set in .env")
        return False
    
    if not settings.reddit_client_secret:
        print("❌ REDDIT_CLIENT_SECRET not set in .env")
        return False
    
    print(f"✅ Reddit Client ID: {settings.reddit_client_id[:10]}...")
    print(f"✅ Reddit User Agent: {settings.reddit_user_agent}")
    return True


def test_reddit_connection():
    """Test if we can connect to Reddit API"""
    print("\n🔍 Testing Reddit API connection...")
    
    try:
        client = RedditClient()
        subreddits = client.search_subreddits("technology", limit=3)
        
        if subreddits:
            print(f"✅ Successfully connected to Reddit API")
            print(f"✅ Found {len(subreddits)} subreddits:")
            for sub in subreddits:
                print(f"   - r/{sub['name']} ({sub['subscribers']:,} subscribers)")
            return True
        else:
            print("❌ No subreddits found (API might be down)")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Reddit API: {e}")
        return False


def test_subreddit_posts():
    """Test if we can fetch posts from a subreddit"""
    print("\n🔍 Testing post fetching...")
    
    try:
        client = RedditClient()
        posts = client.get_new_posts("python", limit=5)
        
        if posts:
            print(f"✅ Successfully fetched {len(posts)} posts from r/python")
            print(f"✅ Latest post: \"{posts[0]['title'][:60]}...\"")
            return True
        else:
            print("⚠️  No posts found (might be normal)")
            return True
            
    except Exception as e:
        print(f"❌ Failed to fetch posts: {e}")
        return False


def test_llm_search_queries():
    """Test if LLM can generate search queries"""
    print("\n🔍 Testing LLM search query generation...")
    
    try:
        service = RedditDiscoveryService()
        queries = service.generate_search_queries(
            "I sell project management SaaS for small teams"
        )
        
        if queries:
            print(f"✅ Successfully generated {len(queries)} search queries:")
            for query in queries:
                print(f"   - {query}")
            return True
        else:
            print("❌ No queries generated")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate queries: {e}")
        return False


def main():
    print("=" * 60)
    print("Reddit Lead Generation - Setup Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Credentials
    results.append(("Credentials", test_reddit_credentials()))
    
    # Test 2: API Connection
    if results[0][1]:  # Only if credentials are set
        results.append(("API Connection", test_reddit_connection()))
        results.append(("Post Fetching", test_subreddit_posts()))
    
    # Test 3: LLM Integration
    results.append(("LLM Integration", test_llm_search_queries()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Reddit lead generation is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        print("\nSetup guide:")
        print("1. Get Reddit API credentials: https://www.reddit.com/prefs/apps")
        print("2. Add to .env:")
        print("   REDDIT_CLIENT_ID=your_client_id")
        print("   REDDIT_CLIENT_SECRET=your_client_secret")
        print("3. Configure LLM (Gemini or OpenAI)")


if __name__ == "__main__":
    main()

