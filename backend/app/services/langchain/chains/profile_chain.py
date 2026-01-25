"""
Profile Summary Chain

LangChain 实现的 ProfileSummaryGenerator
"""
import logging
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.profile import create_profile_summary_prompt


logger = logging.getLogger(__name__)


@lru_cache()
def create_profile_summary_chain():
    """创建 Profile Summary chain"""
    llm = get_llm()
    prompt = create_profile_summary_prompt()
    output_parser = StrOutputParser()
    
    chain = prompt | llm | output_parser
    
    return chain


class ProfileSummaryChainService:
    """
    LangChain 版本的 ProfileSummaryGenerator
    
    与原有接口兼容。
    """
    
    def __init__(self):
        self.chain = create_profile_summary_chain()
    
    def generate(self, profile: dict, posts: list[dict]) -> str:
        """
        生成 Instagram 创作者的摘要
        
        Args:
            profile: 创作者资料
            posts: 最近的帖子列表
            
        Returns:
            1-2 句话的摘要
        """
        try:
            # 提取所需字段
            full_name = profile.get("fullName", "")
            biography = profile.get("biography", "")
            business_category = profile.get("businessCategoryName", "")
            hashtags = profile.get("hashtags", [])
            followers_count = profile.get("followersCount", 0)
            
            # 提取最近的标题
            captions = [post.get("caption", "") for post in posts if post]
            captions_text = "\n".join(f"- {cap[:100]}..." if len(cap) > 100 else f"- {cap}" 
                                     for cap in captions[:8])
            
            # 调用 chain
            result = self.chain.invoke({
                "full_name": full_name,
                "biography": biography,
                "business_category": business_category,
                "hashtags": ", ".join(hashtags) if hashtags else "None",
                "followers_count": followers_count,
                "captions": captions_text or "No captions available"
            })
            
            logger.info("LangChain profile summary generated")
            return result.strip()
        except Exception as e:
            logger.error("ProfileSummaryChainService error: %s", e)
            raise


# 便捷函数
def generate_profile_summary(profile: dict, posts: list[dict]) -> str:
    """快速生成 profile summary"""
    service = ProfileSummaryChainService()
    return service.generate(profile, posts)

