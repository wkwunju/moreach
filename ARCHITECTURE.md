# Moreach 系统架构文档

> **完整的系统架构说明**
> 
> 包含 Instagram 影响者发现和 Reddit 线索生成两个核心功能

---

## 📖 目录

1. [系统概览](#系统概览)
2. [Instagram 影响者发现](#instagram-影响者发现)
3. [Reddit 线索生成](#reddit-线索生成)
4. [数据架构](#数据架构)
5. [技术栈](#技术栈)

---

## 系统概览

### 核心功能

Moreach 是一个 AI 驱动的营销工具平台，提供：

1. **Instagram 影响者发现**
   - Google 搜索 + Instagram 抓取
   - LLM 分析和排序
   - 向量化搜索（Pinecone）
   - SQLite 数据存储

2. **Reddit 线索生成**
   - AI 驱动的 subreddit 发现
   - 中心化去重轮询
   - 成本优化的线索评分
   - 自动生成回复建议

### 技术架构

```
┌─────────────────────────────────────────────────┐
│              前端 (Next.js)                      │
│  • 用户界面                                       │
│  • API 调用                                       │
└─────────────────────────────────────────────────┘
                      ↓ HTTP
┌─────────────────────────────────────────────────┐
│          后端 API (FastAPI)                      │
│  • REST API 端点                                 │
│  • 业务逻辑层                                     │
└─────────────────────────────────────────────────┘
                      ↓
┌──────────┬──────────┬──────────┬──────────┐
│ Services │ Providers│ Workers  │ Models   │
└──────────┴──────────┴──────────┴──────────┘
     ↓          ↓          ↓          ↓
┌─────────────────────────────────────────────────┐
│  外部服务                                         │
│  • SQLite (本地数据库)                            │
│  • Pinecone (向量搜索)                           │
│  • Gemini/OpenAI (LLM)                          │
│  • Reddit API (社交数据)                         │
│  • Apify (Instagram/Google)                     │
│  • Redis (任务队列)                              │
└─────────────────────────────────────────────────┘
```

---

## Instagram 影响者发现

### 核心架构

Instagram 影响者发现系统采用 **SQLite 为主，Pinecone 为辅** 的数据架构：

```
用户输入 → Intent Analysis → Google Dork → Google Search
    ↓
Instagram Scraping → LLM Analysis → SQLite (主数据源)
    ↓                                    ↓
Vector Search ← Pinecone (搜索索引) ← Sync
    ↓
返回结果 ← SQLite (完整数据)
```

**核心原则**：
- ✅ SQLite 是唯一的数据源 (Single Source of Truth)
- ✅ Pinecone 只用于向量搜索
- ✅ 先写 SQLite，再同步 Pinecone
- ✅ 搜索返回 handles，再从 SQLite 查询完整数据

### 主要服务

```
backend/app/services/discovery/
├── manager.py       # 协调器：请求管理、结果存储
├── pipeline.py      # 流程：发现 → 分析 → 存储 → 搜索
└── search.py        # 向量搜索和排序

backend/app/services/llm/
├── intent.py        # 意图分析
├── dork.py          # Google Dork 生成
├── profile_*.py     # Profile 分析（summary, audience, collaboration）

backend/app/providers/
├── apify/           # 数据抓取
├── google/          # Google 搜索
└── instagram/       # Instagram 抓取
```

**详细设计**: 见 [IG_DESIGN.md](IG_DESIGN.md)

---

## Reddit 线索生成

### 核心架构

Reddit 线索生成系统采用 **中心化去重轮询** 和 **成本优化漏斗** 设计：

```
业务描述 → AI 生成查询 → 发现 Subreddits → 用户选择
    ↓
Celery Beat (每6小时) → 中心化轮询 → 去重抓取
    ↓
关键词过滤 (免费，70-90% 过滤) → LLM 分析 (付费)
    ↓
创建线索 → 分发到所有相关 campaign
    ↓
用户查看 → AI 建议回复 → 互动标记
```

**核心原则**：
- ✅ 中心化轮询：多个 campaign 共享同一 subreddit，只抓取一次
- ✅ 成本优化：先关键词过滤（免费），再 LLM 分析（付费），节省 80% 成本
- ✅ 先保存后评分：数据安全，逐个评分并立即 commit
- ✅ 离散评分档位：100/80/70/60/50/0，宽松标准

### 主要服务

```
backend/app/services/reddit/
├── discovery.py      # Subreddit 发现和排序
├── polling.py        # 中心化去重轮询
└── scoring.py        # 两阶段成本优化评分

backend/app/providers/reddit/
└── apify.py          # Apify Reddit Scraper
    ├── Community Search Actor
    └── Reddit Scraper Actor

backend/app/workers/
├── celery_app.py     # 定时任务配置
└── tasks.py          # poll_reddit_leads 任务
```

**详细设计**: 见 [REDDIT_DESIGN.md](REDDIT_DESIGN.md)

---

## 数据架构

### Instagram 影响者数据

```sql
-- 主表：影响者
CREATE TABLE influencers (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE,
    name TEXT,
    bio TEXT,
    profile_summary TEXT,        -- LLM 生成
    category TEXT,
    tags TEXT,
    
    -- 基础指标
    followers FLOAT,
    avg_likes FLOAT,
    avg_comments FLOAT,
    avg_video_views FLOAT,
    
    -- 峰值指标
    highest_likes FLOAT,
    highest_comments FLOAT,
    highest_video_views FLOAT,
    
    -- 帖子分析
    post_sharing_percentage FLOAT,
    post_collaboration_percentage FLOAT,
    
    -- LLM 分析
    audience_analysis TEXT,
    collaboration_opportunity TEXT,
    
    -- 联系信息
    email TEXT,
    external_url TEXT,
    
    -- 其他
    platform TEXT,
    country TEXT,
    gender TEXT,
    profile_url TEXT,
    created_at DATETIME
);

-- 搜索请求
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    created_at DATETIME,
    status TEXT,  -- PARTIAL, PROCESSING, DONE, FAILED
    description TEXT,
    constraints TEXT,
    intent TEXT,
    query_embedding TEXT
);

-- 请求结果（引用）
CREATE TABLE request_results (
    id INTEGER PRIMARY KEY,
    request_id INTEGER,
    influencer_id INTEGER,
    score FLOAT,     -- 来自 Pinecone
    rank INTEGER,
    FOREIGN KEY (request_id) REFERENCES requests(id),
    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
);
```

### Reddit 线索数据

```sql
-- Campaign
CREATE TABLE reddit_campaigns (
    id INTEGER PRIMARY KEY,
    created_at DATETIME,
    updated_at DATETIME,
    status TEXT,  -- DISCOVERING, ACTIVE, PAUSED, COMPLETED
    business_description TEXT,
    keywords TEXT,
    search_queries TEXT,  -- JSON
    poll_interval_hours INTEGER,
    last_poll_at DATETIME
);

-- Campaign Subreddit
CREATE TABLE reddit_campaign_subreddits (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    subreddit_name TEXT,
    subreddit_title TEXT,
    subreddit_description TEXT,
    subscribers INTEGER,
    is_active BOOLEAN,
    created_at DATETIME,
    FOREIGN KEY (campaign_id) REFERENCES reddit_campaigns(id)
);

-- 线索
CREATE TABLE reddit_leads (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    reddit_post_id TEXT UNIQUE,
    subreddit_name TEXT,
    title TEXT,
    content TEXT,
    author TEXT,
    post_url TEXT,
    score INTEGER,
    num_comments INTEGER,
    created_utc FLOAT,
    
    -- AI 分析
    relevancy_score FLOAT,
    relevancy_reason TEXT,
    suggested_comment TEXT,
    suggested_dm TEXT,
    
    status TEXT,  -- NEW, REVIEWED, CONTACTED, DISMISSED
    discovered_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (campaign_id) REFERENCES reddit_campaigns(id)
);

-- 全局轮询追踪
CREATE TABLE global_subreddit_polls (
    id INTEGER PRIMARY KEY,
    subreddit_name TEXT UNIQUE,
    last_poll_at DATETIME,
    last_post_timestamp FLOAT,
    poll_count INTEGER,
    total_posts_found INTEGER
);
```

### 数据关系

```
Instagram:
requests (1) ──< (many) request_results
                          ↓
                   (many) >── (1) influencers

Reddit:
reddit_campaigns (1) ──< (many) reddit_campaign_subreddits
       │
       │ (1)
       └──< (many) reddit_leads

global_subreddit_polls (独立追踪)
```

---

## 技术栈

### 后端

- **Framework**: FastAPI 0.115.0
- **Database**: SQLite (SQLAlchemy 2.0.34)
- **Task Queue**: Celery 5.4.0 + Redis 5.0.8
- **Vector DB**: Pinecone
- **LLM**: Gemini (google-genai 0.7.0) / OpenAI

### 外部服务

- **Apify**: Instagram scraping, Google search
- **PRAW**: Reddit API (7.7.1)
- **Pinecone**: 向量搜索
- **Gemini/OpenAI**: LLM 分析

### 前端

- **Framework**: Next.js
- **Styling**: Tailwind CSS
- **Language**: TypeScript

### 开发工具

- **API Client**: httpx 0.27.2
- **Environment**: python-dotenv 1.0.1
- **Validation**: pydantic 2.8.2

---

## 部署架构

### 开发环境

```
终端 1: FastAPI Server
python -m app.main

终端 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

终端 3: Celery Beat (定期任务)
celery -A app.workers.celery_app beat --loglevel=info

终端 4: Redis
redis-server

前端:
cd frontend && npm run dev
```

### 生产环境（建议）

```
┌─────────────────────────────────────────┐
│         Nginx (反向代理)                 │
└─────────────────────────────────────────┘
           │
           ├─ /api → FastAPI (Gunicorn)
           └─ / → Next.js (静态文件)

FastAPI → Celery Workers (多进程)
       → Celery Beat (单进程)
       → Redis
       → SQLite / PostgreSQL
```

**服务配置**：
- **FastAPI**: Gunicorn + Uvicorn workers
- **Celery**: 4-8 workers
- **Redis**: 持久化配置
- **Database**: 升级到 PostgreSQL（生产推荐）

---

## 性能考虑

### Instagram 发现

- **Google Search**: ~10 秒/查询
- **Instagram Scraping**: ~5 秒/profile
- **LLM Analysis**: ~2 秒/profile
- **总时间**: ~30-50 个 profile 需要 5-10 分钟

**优化建议**：
- 并行处理多个 profile
- 缓存 Google 搜索结果
- 批量 LLM 请求

### Reddit 轮询

- **Subreddit Poll**: ~10 秒/subreddit
- **关键词过滤**: 瞬时（<0.1 秒/帖子）
- **LLM 分析**: ~1-2 秒/帖子
- **总时间**: 100 个 subreddit ~20 分钟

**优化建议**：
- 调整轮询频率（默认 6 小时）
- 提高关键词过滤阈值（减少 LLM 调用）
- 使用更快的 LLM（Gemini Flash）

---

## 安全考虑

### API 密钥

- ✅ 所有密钥存储在 `.env` 文件
- ✅ `.env` 在 `.gitignore` 中
- ❌ 不要硬编码密钥

### 速率限制

- **Reddit API**: 100 请求/分钟（内置限制）
- **Apify**: 根据套餐
- **Gemini**: 60 请求/分钟（免费层）

### 数据隐私

- ✅ 只存储公开数据
- ✅ 遵守 Reddit/Instagram ToS
- ✅ 不存储用户密码

---

## 监控与日志

### 日志级别

```python
# 开发
logging.basicConfig(level=logging.DEBUG)

# 生产
logging.basicConfig(level=logging.INFO)
```

### 关键指标

**Instagram**：
- 搜索请求数
- 发现的影响者数
- LLM 调用次数
- 错误率

**Reddit**：
- 活跃 campaign 数
- 轮询周期时间
- 线索生成数
- LLM 成本

### 错误追踪

```python
# 在代码中
try:
    result = risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
    # 可选：发送到 Sentry 等服务
```

---

## 总结

### 架构原则

1. **单一数据源**: SQLite 是所有数据的唯一真相
2. **职责分离**: Pinecone 只做搜索，不做存储
3. **成本优化**: 多阶段过滤减少 LLM 调用
4. **可扩展性**: 中心化去重轮询
5. **数据一致性**: 先写 SQLite，再同步 Pinecone

### 最佳实践

1. **永远不要**从 Pinecone metadata 创建/更新 Influencer
2. **永远**先写 SQLite，再写 Pinecone
3. **永远**从 SQLite 读取完整数据
4. **定期**检查 SQLite ↔ Pinecone 一致性
5. **监控** LLM 调用成本

---

## 相关文档

- [README.md](README.md) - 项目概览和快速开始
- [IG_DESIGN.md](IG_DESIGN.md) - Instagram 功能完整文档
- [REDDIT_DESIGN.md](REDDIT_DESIGN.md) - Reddit 功能完整文档
- [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) - LangChain 使用指南

---

**文档版本**: 2.0  
**最后更新**: 2026-01-21  
**变更**: 精简架构文档，具体实现细节迁移到各模块设计文档

