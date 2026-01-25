"""
Collaboration Analysis Chain

LangChain 实现的 CollaborationAnalyzer
"""
import logging
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.collaboration import create_collaboration_analysis_prompt


logger = logging.getLogger(__name__)


@lru_cache()
def create_collaboration_analysis_chain():
    """创建 Collaboration Analysis chain"""
    llm = get_llm()
    prompt = create_collaboration_analysis_prompt()
    output_parser = StrOutputParser()
    
    chain = prompt | llm | output_parser
    
    return chain


class CollaborationAnalysisChainService:
    """
    LangChain 版本的 CollaborationAnalyzer
    
    与原有接口兼容。
    """
    
    def __init__(self):
        self.chain = create_collaboration_analysis_chain()
    
    def analyze(self, profile: dict, posts: list[dict], business_description: str = "") -> str:
        """
        分析与创作者的合作机会
        
        Args:
            profile: 创作者资料
            posts: 最近的帖子列表
            business_description: 业务描述（可选）
            
        Returns:
            2-3 句话的合作机会分析
        """
        try:
            # 提取 profile 字段
            handle = profile.get("username", "")
            full_name = profile.get("fullName", "")
            biography = profile.get("biography", "")
            business_category = profile.get("businessCategoryName", "")
            followers_count = profile.get("followersCount", 0)
            
            # 提取合作指标
            collaboration_data = {
                "has_brand_mentions": False,
                "sponsored_posts": 0,
                "product_showcases": 0,
                "common_hashtags": [],
            }
            
            for post in posts[:10]:
                caption = post.get("caption", "").lower()
                mentions = post.get("mentions", [])
                hashtags = post.get("hashtags", [])
                
                # 检测赞助内容
                if any(keyword in caption for keyword in ["#ad", "#sponsored", "#partner", "partnership"]):
                    collaboration_data["sponsored_posts"] += 1
                
                if mentions:
                    collaboration_data["has_brand_mentions"] = True
                
                collaboration_data["common_hashtags"].extend(hashtags[:5])
            
            # 构建业务上下文
            business_context = ""
            if business_description:
                business_context = f"Business context: {business_description}"
            
            # 调用 chain
            result = self.chain.invoke({
                "handle": handle,
                "full_name": full_name,
                "biography": biography,
                "business_category": business_category,
                "followers_count": followers_count,
                "has_brand_mentions": "Yes" if collaboration_data["has_brand_mentions"] else "No",
                "sponsored_posts": collaboration_data["sponsored_posts"],
                "product_showcases": collaboration_data["product_showcases"],
                "common_hashtags": ", ".join(collaboration_data["common_hashtags"][:10]) or "None",
                "business_context": business_context
            })
            
            logger.info("LangChain collaboration analysis generated")
            return result.strip()
        except Exception as e:
            logger.error("CollaborationAnalysisChainService error: %s", e)
            raise


# 便捷函数
def analyze_collaboration(profile: dict, posts: list[dict], business_description: str = "") -> str:
    """快速分析合作机会"""
    service = CollaborationAnalysisChainService()
    return service.analyze(profile, posts, business_description)

