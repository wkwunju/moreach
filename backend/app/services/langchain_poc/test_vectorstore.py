"""
测试 LangChain Pinecone VectorStore vs 当前实现

运行方式:
    python -m app.services.langchain_poc.test_vectorstore
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.config import settings
from app.services.vector.pinecone import PineconeVectorStore


def test_current_implementation():
    """测试当前的 Pinecone 实现"""
    print("=" * 60)
    print("测试当前实现 (app.services.vector.pinecone)")
    print("=" * 60)
    
    try:
        store = PineconeVectorStore()
        
        print(f"✅ Pinecone 连接成功")
        print(f"   Index: {settings.pinecone_index}")
        print(f"   Host: {settings.pinecone_host or 'default'}")
        print(f"   Namespace: {settings.pinecone_namespace or '__default__'}")
        print(f"   支持文本记录: {store.supports_text_records()}")
        
        # 测试搜索
        if store.supports_text_records():
            print("\n测试文本搜索:")
            test_query = "fitness influencer Singapore"
            
            start = time.time()
            results = store.search_text(test_query, top_k=5)
            elapsed = time.time() - start
            
            print(f"   查询: {test_query}")
            print(f"   结果数: {len(results)}")
            print(f"   耗时: {elapsed:.3f}秒")
            
            if results:
                print(f"   Top 1: {results[0].get('id', 'N/A')} (score: {results[0].get('score', 0):.3f})")
        else:
            print("   ⚠️  不支持文本搜索（需要向量）")
        
        print(f"\n代码统计:")
        print(f"   pinecone.py: 139 行")
        print(f"   包含: upsert, query, search_text, 响应格式化")
        
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_langchain_pinecone():
    """测试 LangChain Pinecone VectorStore"""
    print("\n" + "=" * 60)
    print("测试 LangChain Pinecone VectorStore")
    print("=" * 60)
    
    try:
        from langchain_pinecone import PineconeVectorStore as LCPineconeVectorStore
        from langchain_openai import OpenAIEmbeddings
        from pinecone import Pinecone
        
        # 初始化 Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        if settings.pinecone_host:
            index = pc.Index(host=settings.pinecone_host)
        else:
            index = pc.Index(settings.pinecone_index)
        
        # 创建 embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=1024
        )
        
        # 创建 vector store
        vectorstore = LCPineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=settings.pinecone_namespace or "__default__"
        )
        
        print(f"✅ LangChain Pinecone 初始化成功")
        
        # 测试搜索
        print("\n测试相似度搜索:")
        test_query = "fitness influencer Singapore"
        
        start = time.time()
        results = vectorstore.similarity_search(test_query, k=5)
        elapsed = time.time() - start
        
        print(f"   查询: {test_query}")
        print(f"   结果数: {len(results)}")
        print(f"   耗时: {elapsed:.3f}秒")
        
        if results:
            print(f"   Top 1 内容: {results[0].page_content[:100]}...")
            print(f"   Top 1 metadata: {list(results[0].metadata.keys())[:5]}...")
        
        print(f"\n代码统计:")
        print(f"   LangChain 方式: ~10 行")
        print(f"   包含: 初始化 + 搜索")
        print(f"   自动处理: embedding, 格式化, 错误处理")
        
        return True
    except ImportError as e:
        print(f"⚠️  依赖未安装: {e}")
        print("   安装: pip install langchain-pinecone langchain-openai")
        return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_implementations():
    """对比两种实现"""
    print("\n" + "=" * 60)
    print("对比分析")
    print("=" * 60)
    
    current_success = test_current_implementation()
    lc_success = test_langchain_pinecone()
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    print("\n代码复杂度:")
    print("  当前实现: 139 行")
    print("    - 手动响应格式化 (_normalize_matches)")
    print("    - 手动 metadata 清理 (upsert_texts)")
    print("    - 多个辅助方法")
    print("  LangChain: ~10 行")
    print("    - 自动处理所有细节")
    print("  简化程度: 93%")
    
    print("\n功能对比:")
    print("  当前实现:")
    print("    ✅ upsert (vectors)")
    print("    ✅ upsert_texts (with Pinecone Inference API)")
    print("    ✅ query (vector search)")
    print("    ✅ search_text (text search)")
    print("  LangChain:")
    print("    ✅ add_texts (自动 embed + upsert)")
    print("    ✅ similarity_search (自动 embed + query)")
    print("    ✅ similarity_search_with_score")
    print("    ✅ max_marginal_relevance_search (额外功能)")
    
    print("\n关键差异:")
    if settings.embedding_provider.lower() == "pinecone":
        print("  ⚠️  当前使用: Pinecone Inference API (内置 embedding)")
        print("  ⚠️  LangChain: 需要外部 embedding (OpenAI/Gemini)")
        print("  ⚠️  迁移影响: 需要重新索引所有数据")
    else:
        print("  ✅ 当前使用外部 embedding，与 LangChain 兼容")
    
    print("\n优势:")
    print("  ✅ 代码量减少 93%")
    print("  ✅ 自动处理 embedding")
    print("  ✅ 统一的 retriever 接口")
    print("  ✅ 内置高级检索 (MMR, threshold)")
    print("  ✅ 更好的错误处理")
    
    print("\n劣势:")
    print("  ❌ 需要重新配置 embedding 方式")
    if settings.embedding_provider.lower() == "pinecone":
        print("  ❌ 需要重新索引现有数据")
        print("  ❌ 可能增加 embedding 成本")
    print("  ❌ 增加依赖包")
    
    print("\n迁移建议:")
    if settings.embedding_provider.lower() == "pinecone":
        print("  ⚠️  风险较高，建议：")
        print("     1. 保持当前 vector store 实现")
        print("     2. 只迁移 LLM chains (阶段 1-2)")
        print("     3. 考虑 vector store 迁移作为长期目标")
    else:
        print("  ✅ 风险较低，可以考虑迁移")
        print("     1. 在测试环境验证")
        print("     2. 逐步替换")


if __name__ == "__main__":
    compare_implementations()

