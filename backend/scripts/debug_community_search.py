"""
Debug Apify Reddit Community Search
测试不同的输入格式找到正确的参数
"""
import sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def test_input_format(input_format_name, run_input):
    """测试特定的输入格式"""
    print(f"\n{'='*60}")
    print(f"测试输入格式: {input_format_name}")
    print(f"{'='*60}")
    print(f"输入参数: {run_input}")
    
    actor_id = settings.apify_reddit_community_search_actor
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={settings.apify_token}"
    
    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=run_input)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 201:
                print("✅ 成功！运行已启动")
                return True
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:500]}")
                return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """尝试不同的输入格式"""
    print("🔍 调试 Apify Reddit Community Search\n")
    
    # 格式 1: searchQueries (数组)
    test_input_format("格式1: searchQueries (数组)", {
        "searchQueries": ["SaaS"],
        "maxResults": 5,
        "skipNSFW": True,
    })
    
    # 格式 2: query (字符串)
    test_input_format("格式2: query (字符串)", {
        "query": "SaaS",
        "limit": 5,
    })
    
    # 格式 3: search (字符串)
    test_input_format("格式3: search (字符串)", {
        "search": "SaaS",
        "maxResults": 5,
    })
    
    # 格式 4: 最小参数
    test_input_format("格式4: 最小参数", {
        "query": "SaaS",
    })
    
    # 格式 5: Reddit API 格式
    test_input_format("格式5: Reddit API 格式", {
        "searchQuery": "SaaS",
        "limit": 5,
    })
    
    # 格式 6: 空参数（查看默认行为）
    test_input_format("格式6: 空参数", {})
    
    print("\n" + "="*60)
    print("调试完成")
    print("="*60)
    print("\n请查看哪个格式返回了 201 状态码")
    print("然后我们会使用正确的格式更新代码")


if __name__ == "__main__":
    main()

