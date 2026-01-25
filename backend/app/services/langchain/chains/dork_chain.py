"""
Google Dork Generator Chain

LangChain 实现的 GoogleDorkGenerator
"""
import logging
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.dork import create_google_dork_prompt


logger = logging.getLogger(__name__)


@lru_cache()
def create_google_dork_chain():
    """创建 Google Dork Generator chain"""
    llm = get_llm()
    prompt = create_google_dork_prompt()
    output_parser = StrOutputParser()
    
    chain = prompt | llm | output_parser
    
    return chain


class GoogleDorkChainService:
    """
    LangChain 版本的 GoogleDorkGenerator
    
    与原有接口兼容。
    """
    
    def __init__(self):
        self.chain = create_google_dork_chain()
    
    def generate(self, description: str, constraints: str) -> str:
        """
        生成优化的 Google dork 搜索查询
        
        Args:
            description: 业务描述
            constraints: 约束条件
            
        Returns:
            Google dork 查询字符串
        """
        try:
            result = self.chain.invoke({
                "description": description,
                "constraints": constraints
            })
            
            query = result.strip()
            logger.info("LangChain generated Google dork query: %s", query)
            return query
        except Exception as e:
            logger.error("GoogleDorkChainService error: %s", e)
            raise


# 便捷函数
def generate_google_dork(description: str, constraints: str) -> str:
    """快速生成 Google dork 查询"""
    service = GoogleDorkChainService()
    return service.generate(description, constraints)

