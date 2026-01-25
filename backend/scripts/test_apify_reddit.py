"""
Test script for Apify Reddit integration
测试 Apify Reddit 集成
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.reddit.apify import ApifyRedditProvider


def test_community_search():
    """测试 Reddit Community Search actor"""
    print("=" * 60)
    print("测试 Apify Reddit Community Search")
    print("=" * 60)
    
    provider = ApifyRedditProvider()
    
    # 测试搜索
    query = "SaaS startups"
    print(f"\n搜索查询: '{query}'")
    
    communities = provider.search_communities(query, limit=5)
    
    print(f"\n找到 {len(communities)} 个社区:")
    for i, community in enumerate(communities, 1):
        print(f"\n{i}. r/{community['name']}")
        print(f"   标题: {community['title']}")
        print(f"   订阅者: {community['subscribers']:,}")
        print(f"   描述: {community['description'][:100]}...")
        print(f"   URL: {community['url']}")


def test_subreddit_scrape():
    """测试 Reddit Scraper actor"""
    print("\n" + "=" * 60)
    print("测试 Apify Reddit Scraper")
    print("=" * 60)
    
    provider = ApifyRedditProvider()
    
    # 测试抓取
    subreddit = "SaaS"
    print(f"\n抓取 r/{subreddit} (新帖子)")
    
    posts = provider.scrape_subreddit(subreddit, max_posts=5, sort="new")
    
    print(f"\n找到 {len(posts)} 条帖子:")
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post['title']}")
        print(f"   作者: {post['author']}")
        print(f"   得分: {post['score']} | 评论: {post['num_comments']}")
        print(f"   内容: {post['content'][:100]}...")
        print(f"   URL: {post['url']}")


def main():
    """运行所有测试"""
    print("\n🧪 Apify Reddit 集成测试\n")
    
    try:
        # 测试 1: Community Search
        test_community_search()
        
        # 测试 2: Reddit Scraper
        test_subreddit_scrape()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

