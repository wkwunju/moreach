"""
Apify Reddit Providers
使用 Apify actors 替代 PRAW 进行 Reddit 数据抓取
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class ApifyRedditProvider:
    """
    使用 Apify actors 进行 Reddit 数据抓取
    
    两个主要 actors:
    1. Reddit Community Search (bYDdgZhOyVinvqrRI) - 搜索 subreddit
    2. Reddit Scraper (9sHOY9RzPYGjmTHo8) - 抓取 subreddit 内容
    """
    
    def __init__(self):
        self.api_token = settings.apify_token
        self.base_url = "https://api.apify.com/v2"
        self.community_search_actor = settings.apify_reddit_community_search_actor
        self.reddit_scraper_actor = settings.apify_reddit_scraper_actor
        
    def _call_actor(
        self, 
        actor_id: str, 
        run_input: dict,
        timeout: int = 300
    ) -> List[Dict[str, Any]]:
        """
        调用 Apify actor 并等待结果
        
        Args:
            actor_id: Actor ID
            run_input: Actor 输入参数
            timeout: 超时时间（秒）
        
        Returns:
            Actor 运行结果
        """
        try:
            # 启动 actor
            url = f"{self.base_url}/acts/{actor_id}/runs?token={self.api_token}"
            
            with httpx.Client(timeout=timeout) as client:
                logger.info(f"Starting Apify actor {actor_id}")
                response = client.post(url, json=run_input)
                response.raise_for_status()
                
                run_data = response.json()
                run_id = run_data["data"]["id"]
                default_dataset_id = run_data["data"]["defaultDatasetId"]
                
                logger.info(f"Actor run started: {run_id}")
                
                # 等待运行完成
                status_url = f"{self.base_url}/acts/{actor_id}/runs/{run_id}?token={self.api_token}"
                
                max_attempts = timeout // 5  # 每 5 秒检查一次
                for attempt in range(max_attempts):
                    time.sleep(5)
                    
                    status_response = client.get(status_url)
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    status = status_data["data"]["status"]
                    logger.info(f"Actor status: {status} (attempt {attempt + 1}/{max_attempts})")
                    
                    if status == "SUCCEEDED":
                        # 获取结果
                        dataset_url = f"{self.base_url}/datasets/{default_dataset_id}/items?token={self.api_token}"
                        dataset_response = client.get(dataset_url)
                        dataset_response.raise_for_status()
                        
                        results = dataset_response.json()
                        logger.info(f"Actor completed successfully, returned {len(results)} items")
                        
                        # DEBUG: Print first 2 items to see actual field names
                        if results and len(results) > 0:
                            logger.info("=" * 80)
                            logger.info("DEBUG: First item from Apify (showing all fields):")
                            import json
                            logger.info(json.dumps(results[0], indent=2))
                            if len(results) > 1:
                                logger.info("=" * 80)
                                logger.info("DEBUG: Second item from Apify:")
                                logger.info(json.dumps(results[1], indent=2))
                            logger.info("=" * 80)
                        
                        return results
                    
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        logger.error(f"Actor run failed with status: {status}")
                        return []
                
                logger.warning(f"Actor run timed out after {timeout}s")
                return []
                
        except Exception as e:
            logger.error(f"Error calling Apify actor {actor_id}: {e}")
            return []
    
    def search_communities(
        self, 
        search_queries: List[str],  # 改为支持多个关键词
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        使用 Reddit Community Search actor 搜索 subreddit
        支持一次性搜索多个关键词（节省API调用）
        
        Actor: https://console.apify.com/actors/bYDdgZhOyVinvqrRI
        
        Args:
            search_queries: 搜索查询列表（如 ["SaaS startups", "digital marketing"]）
            limit: 最多返回多少个 subreddit
        
        Returns:
            Subreddit 列表，每个包含:
            - name: subreddit 名称
            - title: 标题
            - description: 描述
            - subscribers: 订阅者数量（来自Apify的numberOfMembers字段）
            - url: Reddit URL
            - is_nsfw: 是否NSFW（来自Apify的over18字段）
            - created_utc: 创建时间
        """
        logger.info(f"Searching Reddit communities for {len(search_queries)} queries: {search_queries}")
        
        # 一次性传入所有搜索关键词（节省API调用）
        run_input = {
            "searches": search_queries,  # 支持多个关键词
            "searchCommunities": True,
            "searchPosts": False,
            "searchComments": False,
            "searchUsers": False,
            "maxItems": limit,
            "includeNSFW": False,
            "sort": "new",
            "time": "all",
        }
        
        results = self._call_actor(self.community_search_actor, run_input)
        
        # 标准化输出格式
        communities = []
        for item in results:
            # Safely get numberOfMembers, handling None values
            num_members = item.get("numberOfMembers")
            subscribers = num_members if num_members is not None else 0
            
            communities.append({
                "name": item.get("name", "").replace("r/", ""),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "subscribers": subscribers,  # Fixed: numberOfMembers not subscribers
                "url": item.get("url", ""),
                "is_nsfw": item.get("over18", False),  # Fixed: over18 not nsfw
                "created_utc": item.get("createdAt"),
            })
        
        logger.info(f"Found {len(communities)} communities")
        return communities
    
    def scrape_subreddit(
        self,
        subreddit_name: str,
        max_posts: int = 100,
        sort: str = "new",
        time_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        使用 Reddit Scraper actor 抓取 subreddit 内容
        
        Actor: https://console.apify.com/actors/9sHOY9RzPYGjmTHo8
        
        Args:
            subreddit_name: Subreddit 名称（不带 r/ 前缀）
            max_posts: 最多抓取多少条帖子
            sort: 排序方式 ("new", "hot", "top", "rising")
            time_filter: 时间过滤 ("hour", "day", "week", "month", "year", "all")
        
        Returns:
            帖子列表，每个包含:
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
        logger.info(f"Scraping r/{subreddit_name} (sort={sort}, limit={max_posts}, time={time_filter})")
        
        # 构建 Reddit URL
        base_url = f"https://www.reddit.com/r/{subreddit_name}/"
        
        # 使用完整的 Apify Reddit Scraper 参数（按照用户提供的示例）
        run_input = {
            "startUrls": [{"url": base_url}],
            "withinCommunity": f"r/{subreddit_name}",  # 需要 r/ 前缀
            "searchPosts": True,
            "searchComments": False,
            "searchCommunities": False,
            "searchSort": sort if sort else "new",
            "searchTime": time_filter if time_filter else "all",
            "maxPostsCount": max_posts,
            "maxCommentsCount": 10,
            "maxCommentsPerPost": 10,
            "maxCommunitiesCount": 1,
            "includeNSFW": False,
            "fastMode": True,
            "crawlCommentsPerPost": False,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        }
        
        logger.info(f"Apify config: startUrl={base_url}, withinCommunity={subreddit_name}, sort={sort}, time={time_filter}")
        
        results = self._call_actor(self.reddit_scraper_actor, run_input)
        
        # 标准化输出格式
        posts = []
        for idx, item in enumerate(results):
            # DEBUG: Print raw item fields for first post
            if idx == 0:
                logger.info("=" * 80)
                logger.info("DEBUG: Raw Apify item fields before mapping:")
                logger.info(f"Available keys: {list(item.keys())}")
                logger.info(f"author field: {item.get('author')}")
                logger.info(f"score field: {item.get('score')}")
                logger.info(f"upvotes field: {item.get('upvotes')}")
                logger.info(f"ups field: {item.get('ups')}")
                logger.info(f"numComments field: {item.get('numComments')}")
                logger.info(f"commentCount field: {item.get('commentCount')}")
                logger.info(f"num_comments field: {item.get('num_comments')}")
                logger.info("=" * 80)
            
            # 提取 post ID（从 URL 或直接字段）
            post_id = item.get("id", "")
            if not post_id and "url" in item:
                # 从 URL 提取 ID: https://reddit.com/r/subreddit/comments/POST_ID/...
                parts = item["url"].split("/comments/")
                if len(parts) > 1:
                    post_id = parts[1].split("/")[0]
            
            # 解析时间戳
            created_utc = None
            if "createdAt" in item:
                try:
                    created_dt = datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00"))
                    created_utc = created_dt.timestamp()
                except:
                    pass
            
            # Try multiple possible field names for each value
            # Based on actual Apify output: authorName, upVotes, commentsCount
            author = (item.get("authorName") or          # Apify actual field
                     item.get("author") or 
                     item.get("authorFullname") or 
                     item.get("author_fullname") or 
                     "[deleted]")
            
            score = (item.get("upVotes") or             # Apify actual field
                    item.get("score") or 
                    item.get("upvotes") or 
                    item.get("ups") or 
                    0)
            
            num_comments = (item.get("commentsCount") or  # Apify actual field
                           item.get("numComments") or 
                           item.get("commentCount") or 
                           item.get("num_comments") or 
                           0)
            
            # Map content and URL correctly
            content = (item.get("body") or           # Apify actual field for text posts
                      item.get("selftext") or 
                      "")
            
            url = (item.get("contentUrl") or         # Apify actual field
                  item.get("postUrl") or 
                  item.get("url") or 
                  "")
            
            post_dict = {
                "id": post_id,
                "title": item.get("title", ""),
                "content": content,
                "author": author,
                "score": score,
                "num_comments": num_comments,
                "created_utc": created_utc,
                "url": url,
                "subreddit_name": subreddit_name,
                "flair": item.get("flair", ""),
            }
            
            # DEBUG: Print mapped values for first post
            if idx == 0:
                logger.info("DEBUG: After mapping:")
                logger.info(f"post['author'] = {post_dict['author']}")
                logger.info(f"post['score'] = {post_dict['score']}")
                logger.info(f"post['num_comments'] = {post_dict['num_comments']}")
                logger.info("=" * 80)
            
            posts.append(post_dict)
        
        logger.info(f"Scraped {len(posts)} posts from r/{subreddit_name}")
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
        logger.info(f"Scraping {len(subreddit_names)} subreddits")
        
        # 构建多个 subreddit URLs
        start_urls = []
        for name in subreddit_names:
            url = f"https://www.reddit.com/r/{name}/"
            if sort and sort != "hot":
                url = f"{url}{sort}/"
            start_urls.append({"url": url})
        
        run_input = {
            "startUrls": start_urls,
            "maxItems": len(subreddit_names) * max_posts_per_subreddit,
            "maxPostCount": max_posts_per_subreddit,
            "scrollTimeout": 40,
            "skipComments": True,
        }
        
        results = self._call_actor(self.reddit_scraper_actor, run_input, timeout=600)
        
        # 按 subreddit 分组
        posts_by_subreddit = {name: [] for name in subreddit_names}
        
        for item in results:
            subreddit = item.get("subreddit", "")
            if not subreddit:
                # 尝试从 URL 提取
                url = item.get("url", "")
                if "/r/" in url:
                    subreddit = url.split("/r/")[1].split("/")[0]
            
            if subreddit in posts_by_subreddit:
                # 标准化格式（同上）
                post_id = item.get("id", "")
                if not post_id and "url" in item:
                    parts = item["url"].split("/comments/")
                    if len(parts) > 1:
                        post_id = parts[1].split("/")[0]
                
                created_utc = None
                if "createdAt" in item:
                    try:
                        created_dt = datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00"))
                        created_utc = created_dt.timestamp()
                    except:
                        pass
                
                # Use correct Apify field names
                author = (item.get("authorName") or 
                         item.get("author") or 
                         "[deleted]")
                score = (item.get("upVotes") or 
                        item.get("score") or 
                        item.get("upvotes") or 
                        0)
                num_comments = (item.get("commentsCount") or 
                               item.get("numComments") or 
                               item.get("commentCount") or 
                               0)
                content = (item.get("body") or 
                          item.get("selftext") or 
                          "")
                url = (item.get("contentUrl") or 
                      item.get("postUrl") or 
                      item.get("url") or 
                      "")
                
                posts_by_subreddit[subreddit].append({
                    "id": post_id,
                    "title": item.get("title", ""),
                    "content": content,
                    "author": author,
                    "score": score,
                    "num_comments": num_comments,
                    "created_utc": created_utc,
                    "url": url,
                    "subreddit_name": subreddit,
                    "flair": item.get("flair", ""),
                })
        
        total_posts = sum(len(posts) for posts in posts_by_subreddit.values())
        logger.info(f"Scraped {total_posts} total posts from {len(subreddit_names)} subreddits")
        
        return posts_by_subreddit

