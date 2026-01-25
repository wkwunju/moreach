"""
Audience Analysis Chain

LangChain 实现的 AudienceAnalyzer
"""
import logging
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.audience import create_audience_analysis_prompt


logger = logging.getLogger(__name__)


@lru_cache()
def create_audience_analysis_chain():
    """创建 Audience Analysis chain"""
    llm = get_llm()
    prompt = create_audience_analysis_prompt()
    output_parser = StrOutputParser()
    
    chain = prompt | llm | output_parser
    
    return chain


class AudienceAnalysisChainService:
    """
    LangChain 版本的 AudienceAnalyzer
    
    与原有接口兼容。
    """
    
    def __init__(self):
        self.chain = create_audience_analysis_chain()
    
    def analyze(self, profile: dict, posts: list[dict]) -> str:
        """
        分析创作者的目标受众
        
        Args:
            profile: 创作者资料
            posts: 最近的帖子列表
            
        Returns:
            2-3 句话的受众分析
        """
        try:
            # 提取 profile 字段
            full_name = profile.get("fullName", "")
            biography = profile.get("biography", "")
            business_category = profile.get("businessCategoryName", "")
            followers_count = profile.get("followersCount", 0)
            hashtags = profile.get("hashtags", [])
            
            # 提取 post 数据
            post_data_list = []
            for post in posts[:10]:  # 分析最近 10 个帖子
                post_info = {
                    "caption": post.get("caption", "")[:500],
                    "hashtags": post.get("hashtags", [])[:10],
                    "mentions": post.get("mentions", [])[:5],
                    "likesCount": post.get("likesCount", 0),
                    "commentsCount": post.get("commentsCount", 0),
                    "locationName": post.get("locationName", ""),
                }
                post_data_list.append(post_info)
            
            # 格式化 post 数据为字符串
            post_data_text = "\n".join([
                f"Post {i+1}: Caption: {p['caption'][:100]}..., "
                f"Hashtags: {', '.join(p['hashtags']) if p['hashtags'] else 'None'}, "
                f"Likes: {p['likesCount']}, Comments: {p['commentsCount']}, "
                f"Location: {p['locationName'] or 'N/A'}"
                for i, p in enumerate(post_data_list)
            ])
            
            # 调用 chain
            result = self.chain.invoke({
                "full_name": full_name,
                "biography": biography,
                "business_category": business_category,
                "followers_count": followers_count,
                "hashtags": ", ".join(hashtags) if hashtags else "None",
                "post_data": post_data_text or "No post data available"
            })
            
            logger.info("LangChain audience analysis generated")
            return result.strip()
        except Exception as e:
            logger.error("AudienceAnalysisChainService error: %s", e)
            raise


# 便捷函数
def analyze_audience(profile: dict, posts: list[dict]) -> str:
    """快速分析受众"""
    service = AudienceAnalysisChainService()
    return service.analyze(profile, posts)

