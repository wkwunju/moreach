# Moreach - AI 驱动的营销工具平台

> **智能营销线索发现系统**
> 
> Instagram 影响者发现 + Reddit 线索生成

---

## 📖 快速导航

| 文档 | 用途 | 适用场景 |
|------|------|---------|
| **[README.md](README.md)** | 项目概览和快速开始 | 初次了解项目 ⭐ |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 系统架构总览 | 了解技术架构和设计原则 |
| **[IG_DESIGN.md](IG_DESIGN.md)** | Instagram 功能完整文档 | 使用/开发 Instagram 功能 |
| **[REDDIT_DESIGN.md](REDDIT_DESIGN.md)** | Reddit 功能完整文档 | 使用/开发 Reddit 功能 |
| **[README_AUTH.md](README_AUTH.md)** | 🔐 用户认证系统 | 用户注册登录功能 🆕 |
| **[LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md)** | LangChain 使用指南 | 启用 LangChain 集成（可选）|

---

## ✨ 核心功能

### 0. 用户认证系统 🆕

完整的用户注册和登录系统：
- 🔐 邮箱密码认证
- 🎫 JWT Token 管理
- 👤 用户资料收集（行业、职位、使用类型）
- 🔒 bcrypt 密码加密
- ✅ 前后端双重验证

**快速开始**: [3步启动认证系统](QUICKSTART_AUTH.md)  
**完整文档**: [用户认证系统文档](README_AUTH.md)

### 1. Instagram 影响者发现

自动化的影响者发现流程：
- 🔍 Google 搜索 + Instagram 数据抓取
- 🤖 LLM 驱动的智能分析（支持 LangChain 集成）
- 📊 向量化搜索（Pinecone）
- 💾 SQLite 数据存储

**使用场景**：品牌寻找合适的影响者进行合作

### 2. Reddit 线索生成

智能的 B2B 线索发现：
- 🎯 AI 发现相关 subreddit（使用 Apify Community Search）
- 🔄 自动监控和轮询（使用 Apify Reddit Scraper）
- 💰 成本优化的评分系统（节省 80% LLM 成本）
- 🤖 自动生成回复建议（支持 LangChain 集成）

**使用场景**：B2B 公司从 Reddit 讨论中发现潜在客户

**最新**: 已从 PRAW 迁移到 Apify actors，更稳定可靠 - [查看迁移文档](REDDIT_APIFY_MIGRATION.md)

### 3. LangChain 集成 🆕

可选的 LangChain 集成，提升代码质量和可维护性：
- ✅ 所有 LLM 服务已迁移到 LangChain
- ✅ 代码量减少 60-70%
- ✅ Prompt 模板化管理
- ✅ 统一的 chain 接口
- ⚙️ 通过配置开关启用（`USE_LANGCHAIN_CHAINS=true`）
- 🔄 随时可回滚到原有实现

**查看详情**：[LangChain 迁移指南](LANGCHAIN_MIGRATION_GUIDE.md)

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                      │
│  /try (Instagram)    /reddit (Reddit)                    │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼─────────────────────────────────┐
│              Backend API (FastAPI)                       │
│  /api/v1/requests (IG)  /api/v1/reddit (Reddit)         │
└─────┬──────────────────────────────────────────┬────────┘
      │                                           │
┌─────▼──────────────┐                  ┌────────▼────────┐
│  Instagram Module  │                  │  Reddit Module  │
│  ┌──────────────┐  │                  │  ┌───────────┐  │
│  │ Discovery    │  │                  │  │ Discovery │  │
│  │ Pipeline     │  │                  │  │ Polling   │  │
│  │ Search       │  │                  │  │ Scoring   │  │
│  └──────────────┘  │                  │  └───────────┘  │
└─────┬──────────────┘                  └────────┬────────┘
      │                                           │
┌─────▼─────────────────────────────────────────▼────────┐
│               Shared Services Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   LLM    │  │  Vector  │  │  Apify   │             │
│  │ Services │  │ (Pinecone)│  │ Provider │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────┬─────────────────────────────────────────────────┘
      │
┌─────▼─────────────────────────────────────────────────┐
│              Data & External Services                  │
│  SQLite    Pinecone    Gemini/OpenAI    Redis    Apify│
└───────────────────────────────────────────────────────┘
```

### 共享组件

两个模块共享以下核心服务：

| 服务 | Instagram 用途 | Reddit 用途 | 位置 |
|------|---------------|-------------|------|
| **LLM Services** | Intent parsing, Profile analysis | Query generation, Post scoring | `services/llm/` |
| **Vector Store** | Profile embedding & search | (未使用) | `services/vector/` |
| **Apify Provider** | Google search, IG scraping | Community search, Reddit scraper | `providers/apify/` |
| **SQLite Database** | Influencers, Requests | Campaigns, Leads | `models/tables.py` |
| **Celery Workers** | Async discovery tasks | Scheduled polling (every 6h) | `workers/` |

### 数据隔离

- ✅ **Instagram**: `influencers`, `requests`, `request_results` 表
- ✅ **Reddit**: `reddit_campaigns`, `reddit_leads`, `reddit_campaign_subreddits` 表
- ✅ 完全独立，互不影响

**详细架构**: 见 [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Redis
- API 密钥：
  - Gemini 或 OpenAI
  - Reddit API（用于线索生成）
  - Apify（用于 Instagram）
  - Pinecone

### 1. 克隆项目

```bash
git clone <repo-url>
cd moreach
```

### 2. 配置环境变量

创建 `backend/.env` 文件：

```env
# LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=moreach
PINECONE_HOST=your_pinecone_host

# Apify (用于 Instagram 和 Reddit)
APIFY_TOKEN=your_apify_token

# Database & Redis
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0

# LangChain Integration (可选)
USE_LANGCHAIN_CHAINS=true       # 启用 LangChain LLM chains
USE_LANGCHAIN_EMBEDDINGS=false  # 保持 false（使用 Pinecone Inference）
USE_LANGCHAIN_VECTORSTORE=false # 保持 false
```

### 3. 启动后端服务

```bash
# 终端 1: API 服务器
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main

# 终端 2: Celery Worker
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info

# 终端 3: Celery Beat (Reddit 自动轮询)
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info

# 终端 4: Redis
docker compose up -d
# 或使用本地 Redis: redis-server
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:3000

**可用页面**：
- `/` - 主页
- `/try` - Instagram 影响者发现
- `/reddit` - Reddit 线索生成 ⭐ 新功能

---

## 📚 完整文档

### Instagram 影响者发现

**工作流程**：
```
用户输入描述
    ↓
LLM 解析意图 (共享 LLM Service)
    ↓
Google 搜索 (Apify Google Search Actor)
    ↓
Instagram 抓取 (Apify IG Scraper)
    ↓
LLM 分析 (共享 LLM Service)
    ├─ Profile Summary
    ├─ Audience Analysis
    └─ Collaboration Opportunities
    ↓
存储到 SQLite (主数据源)
    ↓
同步到 Pinecone (向量索引)
    ↓
向量搜索 + 排序
    ↓
返回结果
```

**API 端点**：
- `POST /api/v1/requests` - 创建搜索请求
- `GET /api/v1/requests/{id}` - 查询请求状态
- `GET /api/v1/requests/{id}/results` - 获取结果

**详细文档**: 见 [IG_DESIGN.md](IG_DESIGN.md)

---

### Reddit 线索生成

**工作流程**：
```
用户描述业务
    ↓
LLM 生成搜索查询 (共享 LLM Service)
    ↓
发现 Subreddits (Apify Community Search)
    ↓
用户选择 subreddit
    ↓
Celery Beat 触发 (每 6 小时)
    ↓
中心化轮询 (Apify Reddit Scraper)
    └─ 去重：多个 campaign 共享，只抓取一次
    ↓
先保存后评分
    ├─ 保存所有帖子到 SQLite
    └─ 逐个 LLM 评分并立即 commit
    ↓
分发到所有相关 campaign
    ↓
用户查看 Inbox
    ├─ AI 建议评论
    └─ AI 建议私信
    ↓
一键复制 + 跳转 + 标记状态
```

**API 端点**：
- `POST /api/v1/reddit/campaigns` - 创建 campaign
- `GET /api/v1/reddit/campaigns/{id}/discover-subreddits` - 发现 subreddit
- `POST /api/v1/reddit/campaigns/{id}/select-subreddits` - 激活
- `GET /api/v1/reddit/campaigns/{id}/leads` - 获取线索
- `POST /api/v1/reddit/campaigns/{id}/run-now` - 手动触发轮询

**详细文档**: 见 [REDDIT_DESIGN.md](REDDIT_DESIGN.md)

---

### 跨模块数据流

#### LLM 服务调用

两个模块共享相同的 LLM 客户端和配置：

```
Instagram                 Reddit
    ↓                       ↓
    └──── LLM Client ──────┘
           ↓
    LangChain (可选)
           ↓
    Gemini / OpenAI API
```

**配置开关** (`backend/.env`):
- `USE_LANGCHAIN_CHAINS=true` - 两个模块同时启用 LangChain
- `LLM_PROVIDER=gemini` - 两个模块使用相同的 LLM

#### Apify 服务调用

两个模块使用不同的 Apify Actors：

| 模块 | Actors | 用途 |
|------|--------|------|
| **Instagram** | `google-search-scraper`<br>`instagram-profile-scraper` | Google 搜索<br>IG 数据抓取 |
| **Reddit** | `apify-reddit-api` (Community Search)<br>`reddit-scraper` | Subreddit 搜索<br>帖子抓取 |

#### 数据库结构

```sql
-- Instagram 表（独立）
influencers
requests
request_results

-- Reddit 表（独立）
reddit_campaigns
reddit_campaign_subreddits
reddit_leads
global_subreddit_polls

-- 完全隔离，互不影响
```

---

## 🔧 开发指南

### 项目结构

```
moreach/
├── backend/
│   ├── app/
│   │   ├── api/            # API 端点
│   │   ├── models/         # 数据库模型
│   │   ├── services/       # 业务逻辑
│   │   │   ├── discovery/  # Instagram 发现
│   │   │   ├── reddit/     # Reddit 线索
│   │   │   ├── llm/        # LLM 服务
│   │   │   └── vector/     # 向量搜索
│   │   ├── providers/      # 外部服务
│   │   │   ├── apify/
│   │   │   ├── reddit/
│   │   │   └── instagram/
│   │   └── workers/        # Celery 任务
│   ├── scripts/           # 工具脚本
│   └── requirements.txt
│
├── frontend/
│   ├── app/               # Next.js 页面
│   ├── components/        # React 组件
│   └── lib/              # 工具函数
│
└── 文档/
    ├── README.md          # 本文件
    ├── ARCHITECTURE.md    # 架构文档
    ├── QUICK_START_CN.md  # 详细设置
    └── REDDIT_LEAD_GENERATION.md  # Reddit 功能
```

### 代码规范

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Frontend**: TypeScript, Next.js, Tailwind CSS
- **风格**: 遵循 PEP 8 (Python) 和 ESLint (TypeScript)

### 测试

```bash
# 后端测试
cd backend
python scripts/test_reddit_setup.py

# 前端测试
cd frontend
npm test
```

---

## 📊 性能指标

### Instagram 发现

- **搜索时间**: 5-10 分钟（30-50 个 profile）
- **准确率**: 高（LLM 驱动的分析）
- **成本**: 根据 Apify 和 LLM 使用量

### Reddit 线索生成

- **轮询频率**: 每 6 小时（可配置）
- **成本**: ~$0.80/天/campaign（使用关键词过滤）
- **vs 无过滤**: ~$4.00/天/campaign
- **节省**: 80%

---

## 🔐 安全与隐私

- ✅ 所有 API 密钥存储在环境变量
- ✅ 只收集公开数据
- ✅ 遵守 Reddit/Instagram 服务条款
- ✅ 内置速率限制

---

## 🐛 故障排查

### 常见问题

**Instagram 发现不工作**：
- 检查 Apify token 和配额
- 检查 Pinecone 连接
- 查看 Celery worker 日志

**Reddit 没有线索**：
- 确认 campaign 状态是 ACTIVE
- 检查 Celery Beat 是否运行
- 等待至少一个轮询周期（6 小时）

**详细故障排查**: 见 [REDDIT_LEAD_GENERATION.md#故障排查](REDDIT_LEAD_GENERATION.md#故障排查)

---

## 📖 相关文档

| 文档 | 描述 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构总览，包含两个模块的架构设计 |
| [IG_DESIGN.md](IG_DESIGN.md) | Instagram 影响者发现的完整设计文档 |
| [REDDIT_DESIGN.md](REDDIT_DESIGN.md) | Reddit 线索生成的完整设计文档 |
| [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) | LangChain 集成使用指南 |

---

## 🤝 贡献

欢迎贡献！请遵循以下流程：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📄 许可证

[待定]

---

## 🙏 致谢

- Pinecone - 向量搜索
- Gemini - LLM 服务
- Apify - 数据抓取
- PRAW - Reddit API

---

**版本**: 1.0.0  
**最后更新**: 2026-01-12

**开始使用**: 见 [QUICK_START_CN.md](QUICK_START_CN.md)
