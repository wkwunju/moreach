"""
Reddit Lead Scoring Chain

LangChain 实现的 Reddit Scoring（仅 LLM 分析部分）
"""
import logging
from typing import Dict, Any, Tuple
from functools import lru_cache

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.reddit_scoring import (
    create_reddit_scoring_prompt,
    create_reddit_scoring_parser
)


logger = logging.getLogger(__name__)


@lru_cache()
def create_reddit_scoring_chain():
    """创建 Reddit Scoring chain"""
    llm = get_llm()
    prompt = create_reddit_scoring_prompt()
    parser = create_reddit_scoring_parser()
    
    chain = prompt | llm | parser
    
    return chain


class RedditScoringChainService:
    """
    LangChain 版本的 Reddit Lead Scoring（仅 LLM 部分）
    
    注意：keyword filtering 保留在原有实现中，不用 LangChain
    """
    
    def __init__(self):
        self.chain = create_reddit_scoring_chain()
    
    def llm_analyze(
        self,
        post: Dict[str, Any],
        business_description: str,
        keyword_score: float
    ) -> Tuple[float, str, str, str]:
        """
        使用 LangChain 进行深度 LLM 分析

        Args:
            post: Reddit 帖子数据
            business_description: 业务描述
            keyword_score: 关键词匹配分数

        Returns:
            (relevancy_score, reason, suggested_comment, suggested_dm)
        """
        # 兼容两种字段名：reddit_post_id 或 id（与传统实现保持一致）
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')
        logger.info(f"LangChain analyzing post: {post_id}")
        
        try:
            # 调用 chain（使用 .get() 提供默认值，与传统实现保持一致）
            content = post.get('content', '') or ''
            result = self.chain.invoke({
                "business_description": business_description,
                "title": post.get("title", ""),
                "content": content[:1000],  # 限制 1000 字符
                "subreddit_name": post.get("subreddit_name", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0)
            })

            # 直接使用 LLM 返回的离散分数（100, 90, 80, 70, 60, 50, 0）
            llm_score = result["relevancy_score"]

            # 验证分数是否在允许的离散值中
            allowed_scores = [100, 90, 80, 70, 60, 50, 0]
            if llm_score not in allowed_scores:
                # 找到最接近的允许分数
                llm_score = min(allowed_scores, key=lambda x: abs(x - llm_score))
                logger.warning(f"LLM returned invalid score, snapped to {llm_score}")

            logger.info(
                f"LangChain scored post {post_id}: {llm_score}"
            )

            return (
                llm_score,
                result.get("reason", ""),
                result.get("suggested_comment", ""),
                result.get("suggested_dm", "")
            )
        
        except Exception as e:
            logger.error(f"Error in LangChain Reddit scoring: {e}")
            import traceback
            traceback.print_exc()
            return 50, f"Analysis error: {str(e)}", "", ""


# 便捷函数
def analyze_reddit_lead(
    post: Dict[str, Any],
    business_description: str,
    keyword_score: float
) -> Tuple[float, str, str, str]:
    """快速分析 Reddit 潜在客户"""
    service = RedditScoringChainService()
    return service.llm_analyze(post, business_description, keyword_score)

