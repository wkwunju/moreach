"""
详细调试 Apify actor 调用
"""
import sys
from pathlib import Path
import httpx
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def test_community_search():
    """测试 Community Search actor"""
    print("="*60)
    print("测试 Community Search Actor")
    print("="*60)
    
    actor_id = settings.apify_reddit_community_search_actor
    print(f"Actor ID: {actor_id}")
    
    # 使用您提供的格式
    run_input = {
        "searches": ["SaaS"],
        "searchCommunities": True,
        "searchPosts": False,
        "searchComments": False,
        "searchUsers": False,
        "maxItems": 5,
        "includeNSFW": False,
        "sort": "new",
        "time": "all",
    }
    
    print(f"\n输入参数:")
    print(json.dumps(run_input, indent=2))
    
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={settings.apify_token}"
    print(f"\nURL: {url[:80]}...")
    
    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=run_input)
            
            print(f"\n状态码: {response.status_code}")
            print(f"\n完整响应:")
            print(response.text)
            
            if response.status_code == 201:
                print("\n✅ 成功！")
            else:
                print("\n❌ 失败")
                
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    print(f"\n错误详情:")
                    print(json.dumps(error_data, indent=2))
                except:
                    pass
    except Exception as e:
        print(f"\n❌ 异常: {e}")


def test_actor_info():
    """获取 actor 信息"""
    print("\n" + "="*60)
    print("获取 Actor 信息")
    print("="*60)
    
    actor_id = settings.apify_reddit_community_search_actor
    url = f"https://api.apify.com/v2/acts/{actor_id}?token={settings.apify_token}"
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nActor 名称: {data['data'].get('name', 'N/A')}")
                print(f"Actor 标题: {data['data'].get('title', 'N/A')}")
                print(f"版本: {data['data'].get('version', 'N/A')}")
                
                # 检查输入 schema
                if 'inputSchema' in data['data']:
                    print(f"\n输入 Schema:")
                    print(json.dumps(data['data']['inputSchema'], indent=2)[:500])
            else:
                print(f"\n获取 actor 信息失败: {response.text}")
    except Exception as e:
        print(f"\n异常: {e}")


if __name__ == "__main__":
    test_actor_info()
    print("\n")
    test_community_search()

