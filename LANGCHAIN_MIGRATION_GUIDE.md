# LangChain 迁移指南

## 概述

本指南介绍如何启用和使用项目中的 LangChain 集成。LangChain 已成功集成到所有 LLM 服务中，现在可以通过简单的配置开关启用。

---

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增的依赖包括：
- `langchain==0.3.0`
- `langchain-core==0.3.0`
- `langchain-openai==0.2.0`
- `langchain-google-genai==2.0.0`
- `langchain-pinecone==0.2.0`

### 2. 启用 LangChain

在 `.env` 文件中添加或修改：

```bash
# LangChain feature flags
USE_LANGCHAIN_CHAINS=true        # 启用 LangChain LLM chains
USE_LANGCHAIN_EMBEDDINGS=false   # 暂不推荐
USE_LANGCHAIN_VECTORSTORE=false  # 暂不推荐
```

### 3. 重启服务

```bash
# 重启 API 服务
uvicorn app.main:app --reload

# 重启 Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# 重启 Celery Beat
celery -A app.workers.celery_app beat --loglevel=info
```

### 4. 验证

查看日志，应该看到类似：
```
INFO: Using LangChain IntentChainService
INFO: Using LangChain chains for all LLM services
```

---

## 已迁移的服务

### Instagram Discovery 服务

| 原服务 | LangChain 实现 | 文件位置 |
|--------|---------------|----------|
| `IntentParser` | `IntentChainService` | `app/services/langchain/chains/intent_chain.py` |
| `GoogleDorkGenerator` | `GoogleDorkChainService` | `app/services/langchain/chains/dork_chain.py` |
| `ProfileSummaryGenerator` | `ProfileSummaryChainService` | `app/services/langchain/chains/profile_chain.py` |
| `AudienceAnalyzer` | `AudienceAnalysisChainService` | `app/services/langchain/chains/audience_chain.py` |
| `CollaborationAnalyzer` | `CollaborationAnalysisChainService` | `app/services/langchain/chains/collaboration_chain.py` |

**集成位置**:
- `app/services/discovery/search.py`
- `app/services/discovery/pipeline.py`

### Reddit Lead Generation 服务

| 原服务 | LangChain 实现 | 文件位置 |
|--------|---------------|----------|
| `RedditScoringService.llm_analyze` | `RedditScoringChainService` | `app/services/langchain/chains/reddit_scoring_chain.py` |

**集成位置**:
- `app/services/reddit/scoring.py`

---

## 架构说明

### 目录结构

```
backend/app/services/langchain/
├── __init__.py
├── config.py                    # LLM 统一配置
├── prompts/                     # Prompt 模板
│   ├── __init__.py
│   ├── intent.py
│   ├── dork.py
│   ├── profile.py
│   ├── audience.py
│   ├── collaboration.py
│   └── reddit_scoring.py
└── chains/                      # LangChain chains
    ├── __init__.py
    ├── intent_chain.py
    ├── dork_chain.py
    ├── profile_chain.py
    ├── audience_chain.py
    ├── collaboration_chain.py
    └── reddit_scoring_chain.py
```

### 配置管理

在 `app/services/langchain/config.py` 中统一管理 LLM 配置：

```python
from app.services.langchain.config import get_llm, get_embedding

# 获取配置的 LLM（根据 LLM_PROVIDER 自动选择 OpenAI/Gemini）
llm = get_llm()

# 获取配置的 Embedding（根据 EMBEDDING_PROVIDER 自动选择）
embeddings = get_embedding()
```

### Prompt 模板

所有 prompt 模板集中在 `prompts/` 目录中，便于：
- 版本控制
- A/B 测试
- 多语言支持
- 统一修改

示例：
```python
from app.services.langchain.prompts.intent import create_intent_prompt

prompt = create_intent_prompt()
# PromptTemplate 对象，包含所有变量和模板
```

### LangChain Expression Language (LCEL)

所有 chains 使用 LCEL 语法：

```python
chain = prompt | llm | parser
result = chain.invoke({"variable": "value"})
```

**优势**：
- 简洁明了
- 自动错误处理
- 支持流式输出
- 易于调试和测试

---

## 功能开关详解

### `USE_LANGCHAIN_CHAINS` ✅ 推荐启用

**影响的服务**：
- Intent parsing
- Google dork generation
- Profile summary
- Audience analysis
- Collaboration analysis
- Reddit lead scoring

**优势**：
- 代码减少 60-70%
- Prompt 管理更清晰
- 统一的接口
- 更好的可测试性

**风险**: 低（不涉及数据迁移）

**建议**: ✅ 立即启用

---

### `USE_LANGCHAIN_EMBEDDINGS` ⚠️ 谨慎评估

**当前状态**: 
- 项目使用 Pinecone Inference API（内置 embedding）
- LangChain 需要外部 embedding（OpenAI/Gemini）

**如果启用**:
- 需要切换 `EMBEDDING_PROVIDER` 到 `openai` 或 `gemini`
- 可能增加 embedding 成本
- 不需要重新索引数据（如果向量维度相同）

**建议**: ⚠️ 除非计划切换到外部 embedding，否则保持 `false`

---

### `USE_LANGCHAIN_VECTORSTORE` ❌ 暂不推荐

**当前状态**: 
- `app/services/vector/pinecone.py` 已经稳定
- 与 Pinecone Inference API 集成良好

**如果启用**:
- 需要重新配置 embedding 方式
- 可能需要重新索引所有数据
- 收益不明确（只是代码简化）

**建议**: ❌ 保持 `false`，除非有明确需求（如 RAG 功能）

---

## 回滚机制

如果 LangChain 出现问题，可以立即回滚：

### 方法 1: 配置开关

在 `.env` 中设置：
```bash
USE_LANGCHAIN_CHAINS=false
```

重启服务即可回到旧实现。

### 方法 2: 代码级回滚

所有旧代码都保留在原位：
- `app/services/llm/intent.py`
- `app/services/llm/profile_summary.py`
- 等等

如果需要完全移除 LangChain，只需：
1. 从 `requirements.txt` 删除 LangChain 依赖
2. 删除 `app/services/langchain/` 目录
3. 移除集成代码中的条件逻辑

---

## 测试

### 运行 PoC 测试

在迁移前，可以运行 PoC 测试来验证 LangChain 功能：

```bash
cd backend

# 测试 Embedding
python -m app.services.langchain_poc.test_embedding

# 测试 Vector Store
python -m app.services.langchain_poc.test_vectorstore

# 测试 LLM Chain
python -m app.services.langchain_poc.test_llm_chain
```

### 对比测试

启用 LangChain 后，可以对比新旧实现：

```python
# 在测试环境中
from app.services.llm.intent import IntentParser  # 旧
from app.services.langchain.chains.intent_chain import IntentChainService  # 新

old_parser = IntentParser()
new_parser = IntentChainService()

# 对比结果
old_result = old_parser.parse("fitness influencers", "Singapore")
new_result = new_parser.parse("fitness influencers", "Singapore")

assert old_result == new_result  # 应该相同或非常接近
```

---

## 性能考虑

### LLM 调用成本

LangChain 不会增加 LLM 调用成本：
- 相同的 prompt
- 相同的模型
- 相同的 token 消耗

### 运行时开销

LangChain 增加的开销：
- 首次导入：~50-100ms（仅一次）
- 每次调用：~1-5ms（可忽略）

总体性能影响 < 1%。

### 内存使用

LangChain 依赖包：
- 安装大小：~50MB
- 运行时内存：+10-20MB

对于现代服务器，影响可忽略。

---

## 常见问题

### Q: 启用 LangChain 后 API 报错？

A: 检查依赖是否完全安装：
```bash
pip install -r requirements.txt
```

确保所有 LangChain 包都已安装。

### Q: 输出格式与之前不同？

A: LangChain 的输出解析器可能格式略有不同。检查 `app/services/langchain/prompts/` 中的模板，确保与原有 prompt 一致。

### Q: 性能比之前慢？

A: 首次调用会有缓存预热。后续调用应该与旧实现性能相当。如果持续变慢，请检查：
- 网络延迟
- LLM provider 响应时间
- 日志级别（调试日志会影响性能）

### Q: 想使用 LangChain 的高级功能（如 RAG）？

A: 当前实现是基础集成。如需高级功能：
1. 参考 LangChain 官方文档
2. 在 `app/services/langchain/chains/` 中创建新的 chain
3. 添加到相应服务中

### Q: 如何添加新的 LLM 服务？

A: 按照模式创建：

1. 在 `prompts/` 中创建 prompt 模板
2. 在 `chains/` 中创建 chain
3. 在业务代码中添加配置开关
4. 测试并验证

示例：
```python
# prompts/my_service.py
TEMPLATE = """..."""

def create_my_prompt():
    return PromptTemplate(template=TEMPLATE, input_variables=[...])

# chains/my_service_chain.py
from app.services.langchain.config import get_llm
from app.services.langchain.prompts.my_service import create_my_prompt

def create_my_chain():
    llm = get_llm()
    prompt = create_my_prompt()
    return prompt | llm | StrOutputParser()

class MyChainService:
    def __init__(self):
        self.chain = create_my_chain()
    
    def process(self, input_data):
        return self.chain.invoke(input_data)
```

---

## 下一步

### 立即行动

1. ✅ 安装依赖：`pip install -r requirements.txt`
2. ✅ 启用配置：`USE_LANGCHAIN_CHAINS=true`
3. ✅ 重启服务
4. ✅ 验证日志

### 可选行动

- ⚠️ 评估 embedding 迁移（如果计划切换 provider）
- ❌ 暂不考虑 vector store 迁移

### 监控和反馈

启用 LangChain 后，监控：
- API 响应时间
- LLM token 消耗
- 错误率
- 用户反馈

如有问题，立即回滚到旧实现（`USE_LANGCHAIN_CHAINS=false`）。

---

## 相关文档

- [LangChain 评估报告](LANGCHAIN_EVALUATION.md) - 详细的评估和决策依据
- [LangChain 官方文档](https://python.langchain.com/docs/get_started/introduction)
- [项目架构文档](ARCHITECTURE.md)
- [Reddit Lead Generation](REDDIT_LEAD_GENERATION.md)

---

**更新日期**: 2026-01-12  
**版本**: 1.0.0

