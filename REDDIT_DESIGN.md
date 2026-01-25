# Reddit Lead Generation - 完整设计文档

> **AI 驱动的 Reddit 线索生成系统**
> 
> 从 Reddit 讨论中自动发现、监控和评分潜在客户机会

---

## 📖 目录

1. [系统概述](#系统概述)
2. [核心流程](#核心流程)
3. [技术架构](#技术架构)
4. [数据模型](#数据模型)
5. [前端设计](#前端设计)
6. [后端服务](#后端服务)
7. [评分系统](#评分系统)
8. [API 参考](#api-参考)
9. [配置说明](#配置说明)
10. [使用指南](#使用指南)
11. [优化历史](#优化历史)

---

## 系统概述

### 核心功能

**Reddit Lead Generation** 是一个自动化的线索挖掘系统，通过 AI 技术从 Reddit 讨论中发现和评估潜在客户。

#### 主要特性

1. **智能 Subreddit 发现**
   - LLM 自动生成搜索查询
   - 基于业务描述找到相关社区
   - AI 评分 subreddit 与业务的相关性（0-100分）

2. **自动化监控**
   - 每6小时自动抓取新帖子
   - 去重机制避免重复抓取
   - 只抓取指定时间后的新内容

3. **AI 评分系统**
   - 使用离散评分档位（100/80/70/60/50/0）
   - 宽松评分标准（有关系就给50+分）
   - 每个结果立即写入数据库

4. **AI 生成响应**
   - 自动生成 Suggested Comment
   - 自动生成 Suggested DM
   - 提供相关性原因说明

5. **手动操作工作流**
   - 一键复制 + 跳转 Reddit
   - 自动标记为 Commented/DMed
   - 状态管理干净无残留

### 使用场景

- **B2B SaaS 获客**: 在相关社区发现讨论你产品解决的问题的用户
- **产品验证**: 了解目标用户的真实需求和痛点
- **竞品研究**: 发现用户对竞品的评价和需求
- **社区建设**: 找到潜在的早期用户和推广者

---

## 核心流程

### 完整工作流

```
1. 用户描述业务
   ↓
2. AI 生成搜索关键词
   ↓
3. 调用 Apify 搜索 subreddit（批量）
   ↓
4. 使用 LLM 对每个 subreddit 打分（0-1）
   - 相关性评分: 70%
   - 活跃度评分: 30%（基于订阅数）
   ↓
5. 用户选择要监控的 subreddit
   ↓
6. 每 6 小时自动运行（或手动触发）：
   - 抓取 20 个新帖子/subreddit
   - 先保存到数据库（relevancy_score = None）
   - 然后逐个调用 LLM 评分
   - 立即 commit 每个结果
   - 删除低于 50 分的帖子
   ↓
7. 前端展示（Inbox 风格）：
   - Inbox: 新线索
   - Commented: 已评论
   - DMed: 已私信
   ↓
8. 用户操作：
   - Copy & comment manually → 复制 + 跳转帖子 + 标记 Commented
   - Copy & DM manually → 复制 + 跳转用户页 + 标记 DMed
```

### 数据流优化

#### 优化1: 批量搜索 Subreddit

**之前**: 每个关键词单独调用 Apify
```python
for query in ["SaaS", "startups", "business"]:
    results = search_communities(query)  # 3次API调用
```

**现在**: 一次调用传入所有关键词
```python
results = search_communities(["SaaS", "startups", "business"])  # 1次API调用
```

#### 优化2: 先保存后评分

**之前**: 评分失败导致数据丢失
```python
for post in posts:
    score = llm_score(post)  # ❌ 如果失败，前面的帖子都丢失
    save(post, score)
```

**现在**: 立即保存，然后异步评分
```python
# Step 1: 保存所有帖子
for post in posts:
    save(post, relevancy_score=None)  # ✅ 数据安全
db.commit()

# Step 2: 逐个评分并立即提交
for lead in leads:
    score = llm_score(lead)
    lead.relevancy_score = score
    db.commit()  # ✅ 每个结果立即保存
```

---

## 技术架构

### 技术栈

**后端**:
- FastAPI (API 服务器)
- SQLAlchemy (ORM)
- SQLite (数据库)
- Celery (定时任务)
- Redis (Celery broker)

**前端**:
- Next.js 14 (React 框架)
- TypeScript
- Tailwind CSS

**外部服务**:
- **Apify** (数据抓取)
  - Community Search Actor: 搜索 subreddit
  - Reddit Scraper Actor: 抓取帖子
- **Gemini API** (LLM 服务)
  - 生成搜索查询
  - 评分 subreddit 相关性
  - 评分帖子相关性
  - 生成建议响应

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Campaign   │  │  Subreddit   │  │   Leads       │ │
│  │   Management │  │  Discovery   │  │   Inbox       │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │              API Routes Layer                     │  │
│  │  /campaigns  /discover  /leads  /rescore         │  │
│  └─────────────┬────────────────────────────────────┘  │
│                │                                         │
│  ┌─────────────▼──────────┬─────────────┬────────────┐ │
│  │  Discovery Service     │   Polling   │  Scoring   │ │
│  │  - Generate queries    │   Service   │  Service   │ │
│  │  - Search subreddits   │  - Monitor  │  - Filter  │ │
│  │  - Rank relevance      │  - Dedupe   │  - Score   │ │
│  └────────────────────────┴─────────────┴────────────┘ │
│                │                │              │         │
│  ┌─────────────▼────────────────▼──────────────▼─────┐ │
│  │           Apify Provider       LLM Client          │ │
│  │  - Community Search    - Gemini/OpenAI             │ │
│  │  - Reddit Scraper      - Prompt templates          │ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
│   Apify      │ │   Gemini  │ │  Database   │
│   Actors     │ │    API    │ │   (SQLite)  │
└──────────────┘ └───────────┘ └─────────────┘
```

### Celery 定时任务

```
Celery Beat (Scheduler)
    ↓ 每 6 小时
┌───▼─────────────────────────────┐
│  poll_reddit_leads Task          │
│  1. 获取所有 ACTIVE campaigns    │
│  2. 收集去重后的 subreddits      │
│  3. 对每个 subreddit:            │
│     - 抓取 20 个新帖子           │
│     - 保存到数据库               │
│     - 逐个 LLM 评分              │
│     - 立即 commit                │
│  4. 删除低分帖子 (< 50)          │
└──────────────────────────────────┘
```

---

## 数据模型

### 数据库表结构

#### 1. `reddit_campaigns` - Campaign 管理

```sql
CREATE TABLE reddit_campaigns (
    id INTEGER PRIMARY KEY,
    created_at DATETIME,
    updated_at DATETIME,
    status TEXT,  -- DISCOVERING, ACTIVE, PAUSED, COMPLETED
    business_description TEXT,
    search_queries TEXT,  -- JSON array
    poll_interval_hours INTEGER DEFAULT 6,
    last_poll_at DATETIME
);
```

#### 2. `reddit_campaign_subreddits` - Subreddit 选择

```sql
CREATE TABLE reddit_campaign_subreddits (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    subreddit_name VARCHAR(128),
    subreddit_title VARCHAR(512),
    subreddit_description TEXT,
    subscribers INTEGER,
    relevance_score FLOAT,  -- LLM评分 0.0-1.0
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    FOREIGN KEY(campaign_id) REFERENCES reddit_campaigns(id)
);
```

#### 3. `reddit_leads` - 线索记录

```sql
CREATE TABLE reddit_leads (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    reddit_post_id VARCHAR(128) UNIQUE,
    subreddit_name VARCHAR(128),
    title TEXT,
    content TEXT,
    author VARCHAR(128),
    post_url VARCHAR(512),
    score INTEGER,  -- upvotes
    num_comments INTEGER,
    created_utc FLOAT,
    relevancy_score FLOAT,  -- 可为 NULL（待评分）或 0-100
    relevancy_reason TEXT,
    suggested_comment TEXT,
    suggested_dm TEXT,
    status TEXT,  -- NEW, REVIEWED, CONTACTED, DISMISSED
    discovered_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(campaign_id) REFERENCES reddit_campaigns(id)
);
```

### 状态枚举

#### Campaign 状态

- `DISCOVERING` - 正在查找 subreddit
- `ACTIVE` - 正在监控线索
- `PAUSED` - 暂时停止
- `COMPLETED` - 用户标记为完成

#### Lead 状态

- `NEW` - 新线索（Inbox）
- `REVIEWED` - 已评论（Commented）
- `CONTACTED` - 已私信（DMed）
- `DISMISSED` - 已忽略

**注意**: 前端显示与数据库映射:
- Inbox → NEW
- Commented → REVIEWED
- DMed → CONTACTED

---

## 前端设计

### UI 布局 (Inbox 风格)

```
┌────────────────────────────────────────────────────────────────┐
│  Top Bar: Logo, Navigation                                      │
├──────────┬───────────────────────┬──────────────────────────────┤
│  Left    │      Center           │        Right                 │
│  Sidebar │    Leads List         │    Detail Panel              │
│  (256px) │   (flex-1)            │    (Golden Ratio)            │
│          │                       │                              │
│  ├ Inbox │ ┌──────────────────┐ │ ┌─────────────────────────┐ │
│  ├ Comm. │ │ 🟢 72% relevancy │ │ │ u/author • r/subreddit  │ │
│  └ DMed  │ │ u/xxx • r/SaaS   │ │ │ Post Title              │ │
│          │ │ Looking for PM...│ │ │ Full content...         │ │
│  Filter: │ └──────────────────┘ │ │                         │ │
│  ▼ All   │ ┌──────────────────┐ │ │ 💡 Reasoning:          │ │
│  r/SaaS  │ │ 🟢 65% relevancy │ │ │ User is looking for... │ │
│  r/Start │ │ ...              │ │ │                         │ │
│          │ └──────────────────┘ │ │ 💬 Suggested Comment:  │ │
│          │                       │ │ Have you considered... │ │
│          │                       │ │ [Copy & comment]       │ │
│          │                       │ │                         │ │
│          │                       │ │ 📧 Suggested DM:       │ │
│          │                       │ │ Hi! I saw your post... │ │
│          │                       │ │ [Copy & DM]            │ │
│          │                       │ │                         │ │
│          │                       │ │ [View on Reddit]       │ │
└──────────┴───────────────────────┴──────────────────────────────┘
```

### 可调整宽度

右侧详情面板使用**黄金分割比例**（61.8% : 38.2%）:
- 详情面板: 61.8% 宽度（更宽，方便阅读）
- 列表面板: 38.2% 宽度（紧凑预览）
- 用户可拖动边界调整
- 窗口大小变化时自动重新计算比例

### 状态管理优化

#### 问题: Tab 切换状态残留

**原因**: 
```typescript
// ❌ 错误的方式
setFilterStatus(status);  // 异步更新
handleViewLeads(campaign);  // 使用旧的 filterStatus
```

**解决**:
```typescript
// ✅ 正确的方式
setFilterStatus(status);
await handleViewLeads(campaign, status);  // 直接传递新状态
```

#### 优化: 立即更新 UI

```typescript
async function handleCopyAndComment(lead) {
  await navigator.clipboard.writeText(lead.suggested_comment);
  await handleUpdateStatus(lead.id, "REVIEWED");
  
  // ✅ 立即从列表移除（无需等待API）
  setLeads(prev => prev.filter(l => l.id !== lead.id));
  setSelectedLead(leads.find(l => l.id !== lead.id));
  
  window.open(lead.post_url, '_blank');
}
```

### 前端兼容性

**评分显示** - 支持两种格式:
```typescript
// 兼容旧格式 (0.0-1.0) 和新格式 (0-100)
const score = lead.relevancy_score || 0;
const display = score <= 1 ? Math.round(score * 100) : Math.round(score);
// 0.72 → 72%
// 80 → 80%
```

---

## 后端服务

### 1. Discovery Service (发现服务)

**职责**: 发现和评分 subreddit

**核心方法**:

```python
class RedditDiscoveryService:
    def generate_search_queries(business_description: str) -> List[str]:
        """
        使用 LLM 生成 5-8 个搜索查询
        
        Input: "我销售项目管理 SaaS 给小团队"
        Output: ["project management", "productivity", "SaaS", "small teams"]
        """
    
    def discover_subreddits(search_queries: List[str]) -> List[Dict]:
        """
        批量搜索 subreddit（一次 Apify 调用）
        
        Input: ["SaaS", "startups", "business"]
        Output: [
            {name: "SaaS", subscribers: 50000, ...},
            {name: "startups", subscribers: 800000, ...}
        ]
        """
    
    def rank_subreddits(subreddits: List[Dict], business_desc: str) -> List[Dict]:
        """
        使用 LLM 评分 subreddit 相关性
        
        - 评分档位: 0.0-1.0 (小数)
        - 综合分数: 70% 相关性 + 30% 活跃度
        - 活跃度基于订阅数的对数标准化
        
        Output: 按 composite_score 降序排列
        """
```

### 2. Polling Service (轮询服务)

**职责**: 定期抓取新帖子

**核心方法**:

```python
class RedditPollingService:
    def poll_campaign_immediately(campaign_id: int) -> Dict:
        """
        立即轮询一个 campaign
        
        流程:
        1. 获取 campaign 的所有 subreddit
        2. 对每个 subreddit 抓取 20 个帖子
        3. 先保存到数据库
        4. 逐个 LLM 评分
        5. 删除低分帖子
        """
    
    def poll_subreddit(subreddit_name: str, limit: int = 20) -> List[Dict]:
        """
        抓取单个 subreddit 的新帖子
        
        - 使用 Apify Reddit Scraper
        - sort="new", time_filter="day"
        - 过滤自上次轮询后的帖子
        """
    
    def _distribute_leads_to_campaign(
        campaign_id: int, 
        subreddit: str, 
        posts: List[Dict]
    ) -> int:
        """
        为 campaign 创建 leads
        
        流程:
        1. 检查去重（reddit_post_id）
        2. 保存 lead（score=None）
        3. commit
        4. 逐个评分
        5. commit 每个结果
        6. 删除 < 50 分的
        """
```

### 3. Scoring Service (评分服务)

**职责**: AI 评分帖子相关性

**评分档位** (离散值):
- **100分**: 完美匹配 - 用户明确需要这个解决方案
- **80分**: 强相关 - 高度相关，有明确痛点
- **70分**: 好的线索 - 与业务相关，有潜在机会
- **60分**: 中等线索 - 有一定相关性，值得联系
- **50分**: 弱线索 - 勉强相关但有最低限度的联系
- **0分**: 不是线索 - 完全无关或垃圾内容

**核心方法**:

```python
class RedditScoringService:
    def score_post(post: Dict, business_description: str) -> Dict:
        """
        完整评分流程
        
        返回:
        {
            "relevancy_score": 80,  # 离散档位
            "relevancy_reason": "...",
            "suggested_comment": "...",
            "suggested_dm": "..."
        }
        """
    
    def llm_analyze(post: Dict, business_desc: str) -> Tuple:
        """
        LLM 深度分析
        
        Prompt 要求:
        - 宽松评分标准
        - 只使用指定档位 (100/80/70/60/50/0)
        - 有一点关系就至少给 50 分
        
        返回: (score, reason, comment, dm)
        """
```

**LLM Prompt 策略**:

```
评分指南:
- Be GENEROUS with scoring
- 只要有任何联系就给至少 50 分
- 只有完全无关才给 0 分
- 如果提到行业/话题，至少 50-60 分
- 如果有明确问题可以解决，70+ 分
- 保留 100 分给明确寻求这个解决方案的帖子
```

### 4. Apify Provider (数据抓取)

**职责**: 封装 Apify API 调用

**使用的 Actors**:

1. **Community Search** (`practicaltools~apify-reddit-api`)
   ```python
   search_communities(queries: List[str], limit: int) -> List[Dict]
   ```

2. **Reddit Scraper** (`harshmaur~reddit-scraper`)
   ```python
   scrape_subreddit(
       subreddit: str, 
       max_posts: int = 20,
       sort: str = "new",
       time_filter: str = "day"
   ) -> List[Dict]
   ```

**字段映射** (重要):
```python
# Apify 返回的字段名 → 内部字段名
{
    "numberOfMembers": "subscribers",
    "over18": "is_nsfw",
    "authorName": "author",
    "upVotes": "score",
    "commentsCount": "num_comments",
    "body": "content",
    "contentUrl": "url"
}
```

---

## API 参考

### Campaign 管理

#### POST `/api/v1/reddit/campaigns`
创建新 campaign

**Request**:
```json
{
  "business_description": "我销售项目管理 SaaS 给小团队",
  "poll_interval_hours": 6
}
```

**Response**:
```json
{
  "id": 1,
  "status": "DISCOVERING",
  "search_queries": "[\"project management\", \"SaaS\", ...]",
  "created_at": "2026-01-21T10:00:00"
}
```

#### GET `/api/v1/reddit/campaigns`
列出所有 campaign

#### GET `/api/v1/reddit/campaigns/{id}`
获取 campaign 详情

#### POST `/api/v1/reddit/campaigns/{id}/pause`
暂停 campaign

#### POST `/api/v1/reddit/campaigns/{id}/resume`
恢复 campaign

### Subreddit 发现

#### GET `/api/v1/reddit/campaigns/{id}/discover-subreddits`
发现并评分 subreddit

**Response**:
```json
[
  {
    "name": "SaaS",
    "title": "Software as a Service",
    "subscribers": 50000,
    "relevance_score": 0.95,
    "url": "https://reddit.com/r/SaaS"
  }
]
```

#### POST `/api/v1/reddit/campaigns/{id}/select-subreddits`
选择 subreddit 并激活

**Request**:
```json
{
  "subreddits": [
    {
      "name": "SaaS",
      "subscribers": 50000,
      "relevance_score": 0.95
    }
  ]
}
```

#### GET `/api/v1/reddit/campaigns/{id}/subreddits`
获取 campaign 的 subreddit 列表

### Leads 管理

#### GET `/api/v1/reddit/campaigns/{id}/leads`
获取 leads

**Query Parameters**:
- `status`: NEW/REVIEWED/CONTACTED/DISMISSED
- `limit`: 默认 200
- `offset`: 默认 0

**Response**:
```json
{
  "campaign_id": 1,
  "total_leads": 50,
  "new_leads": 30,
  "leads": [
    {
      "id": 1,
      "title": "Looking for PM tool",
      "relevancy_score": 80,
      "status": "NEW",
      ...
    }
  ]
}
```

#### PATCH `/api/v1/reddit/leads/{id}/status`
更新 lead 状态

**Request**:
```json
{
  "status": "REVIEWED"
}
```

### 运维操作

#### POST `/api/v1/reddit/campaigns/{id}/run-now`
立即运行 campaign（手动触发轮询）

#### POST `/api/v1/reddit/campaigns/{id}/rescore-leads`
重新评分未评分的 leads

---

## 配置说明

### 环境变量

`backend/.env`:

```env
# ==== Apify (必需) ====
APIFY_TOKEN=your_apify_token_here

# Apify Actors (可选，有默认值)
APIFY_REDDIT_COMMUNITY_SEARCH_ACTOR=practicaltools~apify-reddit-api
APIFY_REDDIT_SCRAPER_ACTOR=harshmaur~reddit-scraper

# ==== LLM 配置 ====
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# ==== 数据库 ====
DATABASE_URL=sqlite:///./app.db

# ==== Redis (Celery) ====
REDIS_URL=redis://localhost:6379/0
```

### Celery 调度

`backend/app/workers/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    "poll-reddit-leads": {
        "task": "app.workers.tasks.poll_reddit_leads",
        "schedule": 3600 * 6,  # 每 6 小时
    },
}
```

---

## 使用指南

### 快速开始

#### 1. 启动服务

```bash
# Terminal 1: API 服务器
cd backend
python -m app.main

# Terminal 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (定时任务)
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 4: Frontend
cd frontend
npm run dev
```

#### 2. 创建 Campaign

1. 访问 http://localhost:3000/reddit
2. 点击 "New Campaign"
3. 描述你的业务
4. AI 生成搜索词并发现 subreddit
5. 选择相关的 subreddit
6. 激活 campaign

#### 3. 查看 Leads

1. 等待自动轮询（6小时）或点击 "Run Now"
2. 点击 "View Leads"
3. 在 Inbox 中查看新线索
4. 点击线索查看详情
5. 复制建议内容并前往 Reddit 互动

### 操作工作流

#### Commented 流程

1. 在 Inbox 中选择一个线索
2. 阅读 Suggested Comment
3. 点击 **"Copy & comment manually"**
   - ✅ Comment 复制到剪贴板
   - ✅ 打开 Reddit 帖子页面
   - ✅ 线索标记为 "Commented"
4. 在 Reddit 粘贴并发布评论

#### DMed 流程

1. 在 Inbox 中选择一个线索
2. 阅读 Suggested DM
3. 点击 **"Copy & DM manually"**
   - ✅ DM 复制到剪贴板
   - ✅ 打开 Reddit 用户主页
   - ✅ 线索标记为 "DMed"
4. 点击 "Send Message" 并粘贴 DM

---

## 优化历史

### 2026-01-21: 评分系统重构

**问题**: 所有帖子都是 0 分

**原因**: 
- 关键词过滤太严格
- 评分系统混乱（0-1 vs 0-100）
- 评分失败时缓存数据

**解决**:
1. **改为离散档位** (100/80/70/60/50/0)
2. **宽松评分标准** - 有关系就给 50+ 分
3. **立即写入数据库** - 每个结果立即 commit
4. **前端兼容两种格式** - 自动识别并转换

### 2026-01-20: Subreddit 评分

**问题**: Subreddit 没有相关性评分

**解决**:
1. 添加 `relevance_score` 字段到数据库
2. LLM 评分 subreddit（0.0-1.0）
3. 综合评分: 70% 相关性 + 30% 活跃度
4. 按综合分数排序

### 2026-01-19: 流程优化

**问题**: 
- 每个关键词单独调用 Apify（浪费）
- 评分失败导致数据丢失

**解决**:
1. **批量搜索**: 一次 API 调用传入所有关键词
2. **先保存后评分**: 
   - Step 1: 保存所有帖子（score=None）
   - Step 2: 逐个评分并立即 commit

### 2026-01-18: Apify 迁移

**问题**: PRAW API 不稳定，功能受限

**解决**: 迁移到 Apify
- Community Search Actor
- Reddit Scraper Actor
- 更稳定的数据抓取

### 2026-01-17: UI 重构

**问题**: 列表式布局效率低

**解决**: 
- Inbox 风格三列布局
- 黄金分割比例
- 可拖动调整宽度

### 2026-01-16: 状态管理优化

**问题**: Tab 切换时状态残留

**解决**:
- 传递显式 status 参数
- 立即更新 UI
- 每次切换重新加载数据

---

## 最佳实践

### Campaign 策略

**好的业务描述**:
```
✅ "我销售面向 5-20 人团队的项目管理 SaaS，专注于敏捷开发流程"
✅ "我们帮助电商卖家自动化库存管理和订单处理"
❌ "我销售软件"（太泛）
❌ "最好的项目管理工具"（太营销化）
```

**Subreddit 选择**:
- 选择活跃度高的（每天至少几个新帖）
- 目标受众匹配
- 规则允许讨论工具/解决方案
- 不要选太大的泛用 subreddit（如 r/AskReddit）

### 互动技巧

1. **先提供价值**: 帮助用户，不要太推销
2. **快速响应**: Reddit 节奏快，尽快回复
3. **个性化内容**: 使用 AI 建议作为起点，添加个人化
4. **遵守规则**: 阅读并遵守每个 subreddit 的规则
5. **追踪结果**: 记录哪些有效

### 成本优化

**Apify 使用**:
- 每个 subreddit 只抓 20 个帖子
- 使用 time_filter 减少无用数据
- 批量搜索避免重复调用

**LLM 使用**:
- 先保存后评分（避免重复抓取）
- 删除低分帖子（< 50）
- 使用更便宜的模型（Gemini Flash）

---

## 故障排查

### 问题: 没有找到线索

**检查清单**:
1. Campaign 状态是否为 `ACTIVE`
2. Celery Beat 是否运行
3. 距离上次轮询是否超过 6 小时
4. Subreddit 是否有新帖子

**手动触发**:
```bash
# 方法 1: API
curl -X POST http://localhost:8000/api/v1/reddit/campaigns/1/run-now

# 方法 2: Python
python -c "from app.workers.tasks import poll_reddit_leads; poll_reddit_leads()"
```

### 问题: 所有帖子 0 分

**可能原因**:
1. 使用旧的评分格式（0-1）
2. LLM 评分失败

**解决**:
```bash
# 重新评分
curl -X POST http://localhost:8000/api/v1/reddit/campaigns/1/rescore-leads

# 或转换旧数据
sqlite3 app.db "UPDATE reddit_leads SET relevancy_score = relevancy_score * 100 WHERE relevancy_score <= 1;"
```

### 问题: Tab 切换后数据不对

**原因**: 状态管理 bug（已修复）

**确认修复**: 前端代码应该有:
```typescript
await handleViewLeads(campaign, status);  // ✅ 传递显式 status
```

### 问题: Apify 额度不足

**解决**:
1. 检查 [Apify Console Usage](https://console.apify.com/organization/usage)
2. 升级套餐或购买额度
3. 减少轮询频率（增加小时数）
4. 减少每次抓取的帖子数量

---

## 技术参考

### 代码结构

```
backend/app/
├── api/v1/routes.py              # API 端点
├── models/
│   ├── tables.py                 # 数据库模型
│   └── schemas.py                # Pydantic schemas
├── providers/reddit/
│   └── apify.py                  # Apify 封装
├── services/reddit/
│   ├── discovery.py              # Subreddit 发现
│   ├── polling.py                # 轮询服务
│   └── scoring.py                # 评分服务
├── services/llm/
│   └── client.py                 # LLM 客户端
└── workers/
    ├── celery_app.py             # Celery 配置
    └── tasks.py                  # 后台任务

frontend/app/
├── reddit/page.tsx               # Reddit 页面
├── lib/
│   ├── api.ts                    # API 调用
│   └── types.ts                  # TypeScript 类型
└── components/
    └── Navigation.tsx            # 导航栏
```

### 关键文件

**后端**:
- `backend/app/api/v1/routes.py` (591 行) - 所有 API 端点
- `backend/app/services/reddit/polling.py` (513 行) - 轮询逻辑
- `backend/app/services/reddit/scoring.py` (300 行) - 评分逻辑
- `backend/app/providers/reddit/apify.py` (424 行) - Apify 集成

**前端**:
- `frontend/app/reddit/page.tsx` (1000+ 行) - 完整 UI

---

## 结语

Reddit Lead Generation 是一个完整的、生产就绪的系统，已经过多次优化和修复。

### 核心优势

✅ **AI 驱动** - 自动发现、评分、生成响应  
✅ **成本优化** - 先保存后评分，批量调用  
✅ **用户友好** - Inbox 风格，一键操作  
✅ **稳定可靠** - 完善的错误处理和数据保护  
✅ **高度可配置** - 灵活的评分标准和轮询频率  

### 开始使用

1. 配置 Apify 和 Gemini API
2. 启动所有服务
3. 创建第一个 campaign
4. 等待或手动触发轮询
5. 在 Inbox 中查看和处理线索

祝你获客顺利！🚀

---

**文档版本**: 2.0  
**最后更新**: 2026-01-21  
**维护者**: AI Assistant

