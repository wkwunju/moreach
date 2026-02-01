# LangChain Proof of Concept

This directory contains evaluation test code for LangChain integration.

## Purpose

Evaluate whether LangChain is suitable for the project and assess migration feasibility without modifying existing code.

## File Descriptions

- `test_embedding.py` - Test LangChain embedding vs current implementation
- `test_vectorstore.py` - Test LangChain Pinecone integration
- `test_llm_chain.py` - Test LangChain LLM chains

## Running Tests

### Prerequisites

Install LangChain dependencies:
```bash
pip install langchain langchain-openai langchain-google-genai langchain-pinecone
```

### Running Individual Tests

```bash
cd backend

# Test Embedding
python -m app.services.langchain_poc.test_embedding

# Test Vector Store
python -m app.services.langchain_poc.test_vectorstore

# Test LLM Chain
python -m app.services.langchain_poc.test_llm_chain
```

### Running All Tests

```bash
cd backend
python -m app.services.langchain_poc.test_embedding
python -m app.services.langchain_poc.test_vectorstore
python -m app.services.langchain_poc.test_llm_chain
```

## Key Findings

### Recommended for Migration
- **LLM Chains**: 67% code reduction, low risk, high reward

### Conditional Migration
- **Embedding**: Depends on current embedding method (Pinecone Inference vs external)

### Not Recommended
- **Vector Store**: Current implementation is stable, high migration cost

## Next Steps

If evaluation passes, proceed with:
1. Phase 1: Migrate LLM Chains
2. Phase 2: Evaluate Embedding migration (optional)
3. Phase 3: Evaluate Vector Store migration (not recommended)

See [LANGCHAIN_MIGRATION_GUIDE.md](/LANGCHAIN_MIGRATION_GUIDE.md) for detailed migration instructions.
