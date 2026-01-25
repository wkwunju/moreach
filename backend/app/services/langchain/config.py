"""
LangChain Configuration

统一的 LLM 配置和初始化。
"""
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings


@lru_cache()
def get_llm():
    """获取配置的 LLM 实例"""
    if settings.llm_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.2
        )
    else:
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2
        )


@lru_cache()
def get_embedding():
    """获取配置的 Embedding 实例"""
    from langchain_openai import OpenAIEmbeddings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    
    if settings.embedding_provider == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.gemini_api_key
        )
    else:
        return OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=settings.openai_api_key,
            dimensions=1024
        )

