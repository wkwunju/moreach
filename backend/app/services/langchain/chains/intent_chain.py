"""
Intent Parsing Chain

LangChain 实现的 IntentParser，替代 app.services.llm.intent.IntentParser
"""
import logging
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.intent import create_intent_prompt


logger = logging.getLogger(__name__)


@lru_cache()
def create_intent_chain():
    """创建 Intent 解析 chain"""
    llm = get_llm()
    prompt = create_intent_prompt()
    output_parser = StrOutputParser()
    
    # 使用 LangChain Expression Language (LCEL)
    chain = prompt | llm | output_parser
    
    return chain


class IntentChainService:
    """
    LangChain 版本的 IntentParser
    
    与原有接口兼容，方便切换。
    """
    
    def __init__(self):
        self.chain = create_intent_chain()
    
    def parse(self, description: str, constraints: str) -> str:
        """
        解析用户描述和约束，提取搜索意图
        
        Args:
            description: 业务描述
            constraints: 约束条件
            
        Returns:
            提取的搜索查询字符串
        """
        try:
            result = self.chain.invoke({
                "description": description,
                "constraints": constraints
            })
            
            logger.info("LangChain intent output: %s", result)
            return result.strip()
        except Exception as e:
            logger.error("IntentChainService error: %s", e)
            raise


# 便捷函数
def parse_intent(description: str, constraints: str) -> str:
    """快速解析意图"""
    service = IntentChainService()
    return service.parse(description, constraints)

