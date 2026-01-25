"""
测试 LangChain Embedding vs 当前实现

运行方式:
    python -m app.services.langchain_poc.test_embedding
"""
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.config import settings
from app.services.llm.embeddings import EmbeddingService


def test_current_implementation():
    """测试当前的 embedding 实现"""
    print("=" * 60)
    print("测试当前实现 (app.services.llm.embeddings)")
    print("=" * 60)
    
    try:
        service = EmbeddingService()
        test_text = "Instagram fitness influencer in Singapore with 50K followers"
        
        start = time.time()
        if settings.embedding_provider.lower() == "pinecone":
            print("⚠️  当前使用 Pinecone Inference API (内置 embedding)")
            print("    无法直接测试，因为 embedding 集成在 upsert_records 中")
            return None, None, None
        else:
            vector = service.embed_query(test_text)
            elapsed = time.time() - start
            
            print(f"✅ 成功")
            print(f"   文本: {test_text}")
            print(f"   向量维度: {len(vector)}")
            print(f"   耗时: {elapsed:.3f}秒")
            print(f"   Provider: {settings.embedding_provider}")
            
            return vector, elapsed, len(vector)
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None, None, None


def test_langchain_openai():
    """测试 LangChain OpenAI Embeddings"""
    print("\n" + "=" * 60)
    print("测试 LangChain - OpenAI Embeddings")
    print("=" * 60)
    
    try:
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=1024  # 匹配当前设置
        )
        
        test_text = "Instagram fitness influencer in Singapore with 50K followers"
        
        start = time.time()
        vector = embeddings.embed_query(test_text)
        elapsed = time.time() - start
        
        print(f"✅ 成功")
        print(f"   文本: {test_text}")
        print(f"   向量维度: {len(vector)}")
        print(f"   耗时: {elapsed:.3f}秒")
        print(f"   模型: text-embedding-3-large")
        
        return vector, elapsed, len(vector)
    except ImportError:
        print("⚠️  langchain-openai 未安装")
        print("   安装: pip install langchain-openai")
        return None, None, None
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None, None, None


def test_langchain_gemini():
    """测试 LangChain Google Generative AI Embeddings"""
    print("\n" + "=" * 60)
    print("测试 LangChain - Google Gemini Embeddings")
    print("=" * 60)
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004"
        )
        
        test_text = "Instagram fitness influencer in Singapore with 50K followers"
        
        start = time.time()
        vector = embeddings.embed_query(test_text)
        elapsed = time.time() - start
        
        print(f"✅ 成功")
        print(f"   文本: {test_text}")
        print(f"   向量维度: {len(vector)}")
        print(f"   耗时: {elapsed:.3f}秒")
        print(f"   模型: text-embedding-004")
        
        return vector, elapsed, len(vector)
    except ImportError:
        print("⚠️  langchain-google-genai 未安装")
        print("   安装: pip install langchain-google-genai")
        return None, None, None
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None, None, None


def compare_results():
    """对比测试结果"""
    print("\n" + "=" * 60)
    print("对比分析")
    print("=" * 60)
    
    current_vector, current_time, current_dim = test_current_implementation()
    lc_openai_vector, lc_openai_time, lc_openai_dim = test_langchain_openai()
    lc_gemini_vector, lc_gemini_time, lc_gemini_dim = test_langchain_gemini()
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    print("\n代码复杂度:")
    print("  当前实现: ~45 行（embeddings.py）")
    print("  LangChain: ~3 行（初始化 + 调用）")
    print("  简化程度: 93%")
    
    if current_time and lc_openai_time:
        print(f"\n性能对比 (OpenAI):")
        print(f"  当前: {current_time:.3f}秒")
        print(f"  LangChain: {lc_openai_time:.3f}秒")
        diff_pct = ((lc_openai_time - current_time) / current_time) * 100
        print(f"  差异: {diff_pct:+.1f}%")
    
    if lc_gemini_time:
        print(f"\nGemini 性能:")
        print(f"  LangChain Gemini: {lc_gemini_time:.3f}秒")
    
    print("\n兼容性:")
    if settings.embedding_provider.lower() == "pinecone":
        print("  ⚠️  当前使用 Pinecone Inference API")
        print("  ⚠️  LangChain 默认使用外部 embedding")
        print("  ⚠️  迁移需要切换到 OpenAI/Gemini embedding")
    else:
        print("  ✅ 当前使用外部 embedding，兼容 LangChain")
    
    print("\n优势:")
    print("  ✅ 代码量减少 93%")
    print("  ✅ 统一接口，易于切换模型")
    print("  ✅ 内置错误处理和重试")
    print("  ✅ 支持批量优化")
    
    print("\n劣势:")
    print("  ❌ 增加依赖包")
    if settings.embedding_provider.lower() == "pinecone":
        print("  ❌ 需要从 Pinecone Inference 迁移到外部 embedding")


if __name__ == "__main__":
    compare_results()

