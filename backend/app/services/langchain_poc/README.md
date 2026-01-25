# LangChain Proof of Concept

这个目录包含 LangChain 集成的评估测试代码。

## 目的

在不修改现有代码的情况下，评估 LangChain 是否适合项目，以及迁移的可行性。

## 文件说明

- `test_embedding.py` - 测试 LangChain embedding vs 当前实现
- `test_vectorstore.py` - 测试 LangChain Pinecone 集成
- `test_llm_chain.py` - 测试 LangChain LLM chains

## 运行测试

### 前置要求

安装 LangChain 依赖：
```bash
pip install langchain langchain-openai langchain-google-genai langchain-pinecone
```

### 运行单个测试

```bash
cd backend

# 测试 Embedding
python -m app.services.langchain_poc.test_embedding

# 测试 Vector Store
python -m app.services.langchain_poc.test_vectorstore

# 测试 LLM Chain
python -m app.services.langchain_poc.test_llm_chain
```

### 运行所有测试

```bash
cd backend
python -m app.services.langchain_poc.test_embedding
python -m app.services.langchain_poc.test_vectorstore
python -m app.services.langchain_poc.test_llm_chain
```

## 评估结果

查看 `/LANGCHAIN_EVALUATION.md` 获取完整的评估报告。

## 关键发现

### ✅ 推荐迁移
- **LLM Chains**: 代码减少 67%，风险低，收益高

### ⚠️ 条件性迁移
- **Embedding**: 取决于当前 embedding 方式（Pinecone Inference vs 外部）

### ❌ 暂不推荐
- **Vector Store**: 当前实现稳定，迁移成本高

## 下一步

如果评估通过，继续执行：
1. 阶段 1: 迁移 LLM Chains（2-3 天）
2. 阶段 2: 评估 Embedding 迁移（可选）
3. 阶段 3: 评估 Vector Store 迁移（不推荐）

查看 `/LANGCHAIN_EVALUATION.md` 获取详细计划。

