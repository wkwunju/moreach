"""
RapidAPI Reddit Provider
Plan B: 使用 RapidAPI 替代 Apify 进行 Reddit 数据抓取
"""
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class RapidAPIRedditProvider:
    """
    使用 RapidAPI 进行 Reddit 数据抓取

    API: https://rapidapi.com/reddit60/api/reddit60
    Host: reddit60.p.rapidapi.com
    """

    def __init__(self):
        self.api_key = settings.rapidapi_key
        self.host = settings.rapidapi_reddit_host
        self.base_url = f"https://{self.host}"

    def _make_request(
        self,
        endpoint: str,
        params: dict,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发起 RapidAPI 请求

        Args:
            endpoint: API endpoint (e.g., "/subreddits_search")
            params: Query parameters
            timeout: 超时时间（秒）

        Returns:
            API 响应 JSON
        """
        if not self.api_key or not self.host:
            logger.error("RapidAPI credentials not configured")
            return {"status": "error", "body": {}}

        headers = {
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key,
        }

        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(timeout=timeout) as client:
                logger.info(f"RapidAPI request: {endpoint} with params: {params}")
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                logger.info(f"RapidAPI response status: {data.get('status', 'unknown')}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"RapidAPI HTTP error: {e.response.status_code} - {e.response.text}")
            return {"status": "error", "body": {}}
        except Exception as e:
            logger.error(f"RapidAPI request error: {e}")
            return {"status": "error", "body": {}}

    def search_communities(
        self,
        search_queries: List[str],
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        使用 RapidAPI 搜索 subreddit

        Endpoint: /subreddits_search

        Args:
            search_queries: 搜索查询列表
            limit: 最多返回多少个 subreddit

        Returns:
            Subreddit 列表，格式与 ApifyRedditProvider 一致:
            - name: subreddit 名称
            - title: 标题
            - description: 描述
            - subscribers: 订阅者数量
            - url: Reddit URL
            - is_nsfw: 是否NSFW
            - created_utc: 创建时间
        """
        logger.info(f"RapidAPI: Searching Reddit communities for {len(search_queries)} queries")

        all_communities = {}  # 用于去重

        for query in search_queries:
            params = {"q": query}

            response = self._make_request("/subreddits_search", params)

            if response.get("status") != "success":
                logger.warning(f"RapidAPI search failed for query: {query}")
                continue

            body = response.get("body", {})
            data = body.get("data", {})
            children = data.get("children", [])

            if not children:
                logger.info(f"No results for query: {query}")
                continue

            for item in children:
                if item.get("kind") != "t5":  # t5 = subreddit
                    continue

                sub_data = item.get("data", {})
                name = sub_data.get("display_name", "")

                if not name:
                    continue

                # 跳过 NSFW
                if sub_data.get("over18", False):
                    continue

                # 去重：保留订阅者最多的
                subscribers = sub_data.get("subscribers", 0) or 0
                if name not in all_communities or subscribers > all_communities[name].get("subscribers", 0):
                    all_communities[name] = {
                        "name": name,
                        "title": sub_data.get("title", ""),
                        "description": sub_data.get("public_description", "") or sub_data.get("description", ""),
                        "subscribers": subscribers,
                        "url": f"https://reddit.com{sub_data.get('url', f'/r/{name}/')}",
                        "is_nsfw": sub_data.get("over18", False),
                        "created_utc": sub_data.get("created_utc"),
                    }

            logger.info(f"Query '{query}' returned {len(children)} results")

        communities = list(all_communities.values())

        # 按订阅者数量排序
        communities.sort(key=lambda x: x.get("subscribers", 0), reverse=True)

        # 限制返回数量
        communities = communities[:limit]

        logger.info(f"RapidAPI: Found {len(communities)} unique communities")
        return communities

    def scrape_subreddit(
        self,
        subreddit_name: str,
        max_posts: int = 100,
        sort: str = "new",
        time_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        使用 RapidAPI 抓取 subreddit 内容

        Endpoint: /subreddit_new

        Args:
            subreddit_name: Subreddit 名称（不带 r/ 前缀）
            max_posts: 最多抓取多少条帖子
            sort: 排序方式 (目前仅支持 "new")
            time_filter: 时间过滤 (暂不支持)

        Returns:
            帖子列表，格式与 ApifyRedditProvider 一致:
            - id: Reddit post ID
            - title: 标题
            - content: 内容（selftext）
            - author: 作者
            - score: 得分
            - num_comments: 评论数
            - created_utc: 创建时间
            - url: Reddit URL
            - subreddit_name: Subreddit 名称
        """
        logger.info(f"RapidAPI: Scraping r/{subreddit_name} (max_posts={max_posts})")

        posts = []
        after = None  # 分页游标

        while len(posts) < max_posts:
            params = {"subreddit": subreddit_name}
            if after:
                params["after"] = after

            response = self._make_request("/subreddit_new", params)

            if response.get("status") != "success":
                logger.warning(f"RapidAPI scrape failed for r/{subreddit_name}")
                break

            body = response.get("body", {})
            data = body.get("data", {})
            children = data.get("children", [])

            if not children:
                logger.info(f"No more posts for r/{subreddit_name}")
                break

            for item in children:
                if item.get("kind") != "t3":  # t3 = post
                    continue

                post_data = item.get("data", {})

                # 跳过 NSFW
                if post_data.get("over_18", False):
                    continue

                post = {
                    "id": post_data.get("id", ""),
                    "title": post_data.get("title", ""),
                    "content": post_data.get("selftext", ""),
                    "author": post_data.get("author", "[deleted]"),
                    "score": post_data.get("score", 0) or post_data.get("ups", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc"),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "subreddit_name": subreddit_name,
                    "flair": post_data.get("link_flair_text", ""),
                }
                posts.append(post)

                if len(posts) >= max_posts:
                    break

            # 获取下一页游标
            after = data.get("after")
            if not after:
                break

        logger.info(f"RapidAPI: Scraped {len(posts)} posts from r/{subreddit_name}")
        return posts

    def scrape_multiple_subreddits(
        self,
        subreddit_names: List[str],
        max_posts_per_subreddit: int = 50,
        sort: str = "new"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量抓取多个 subreddit

        Args:
            subreddit_names: Subreddit 名称列表
            max_posts_per_subreddit: 每个 subreddit 最多抓取多少帖子
            sort: 排序方式

        Returns:
            字典，key 是 subreddit 名称，value 是帖子列表
        """
        logger.info(f"RapidAPI: Scraping {len(subreddit_names)} subreddits")

        results = {}
        for name in subreddit_names:
            posts = self.scrape_subreddit(
                subreddit_name=name,
                max_posts=max_posts_per_subreddit,
                sort=sort
            )
            results[name] = posts

        total_posts = sum(len(posts) for posts in results.values())
        logger.info(f"RapidAPI: Scraped {total_posts} total posts from {len(subreddit_names)} subreddits")

        return results

    def fetch_subreddit_rules(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Fetch subreddit rules via /subreddit_rules endpoint.

        Args:
            subreddit_name: Subreddit name (without r/ prefix)

        Returns:
            List of rule dicts with keys: short_name, description, kind, priority
        """
        logger.info(f"RapidAPI: Fetching rules for r/{subreddit_name}")

        data = self._make_request(
            endpoint="/subreddit_rules",
            params={"subreddit": subreddit_name},
            timeout=15
        )

        if data.get("status") != "success":
            logger.warning(f"Failed to fetch rules for r/{subreddit_name}")
            return []

        rules = data.get("body", {}).get("rules", [])
        # Return only useful fields
        return [
            {
                "short_name": rule.get("short_name", ""),
                "description": rule.get("description", ""),
                "kind": rule.get("kind", "all"),
                "priority": rule.get("priority", 0),
            }
            for rule in rules
        ]
