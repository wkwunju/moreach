# Instagram 影响者发现 - 完整设计文档

> **AI 驱动的 Instagram 影响者发现系统**
> 
> 通过 Google 搜索和 Instagram 抓取，自动发现、分析和推荐相关影响者

---

## 📖 目录

1. [系统概述](#系统概述)
2. [核心流程](#核心流程)
3. [技术架构](#技术架构)
4. [数据模型](#数据模型)
5. [数据同步策略](#数据同步策略)
6. [前端设计](#前端设计)
7. [后端服务](#后端服务)
8. [API 参考](#api-参考)
9. [配置说明](#配置说明)
10. [使用指南](#使用指南)
11. [最佳实践](#最佳实践)

---

## 系统概述

### 核心功能

**Instagram Influencer Discovery** 是一个智能化的影响者发现系统，通过 AI 技术自动从 Instagram 发现和分析符合品牌需求的影响者。

#### 主要特性

1. **智能意图分析**
   - LLM 解析用户需求
   - 提取行业、地点、约束条件
   - 生成优化的搜索策略

2. **Google Dork 搜索**
   - AI 生成精准搜索查询
   - 自动查找 Instagram profiles
   - 返回候选人列表

3. **Instagram 数据抓取**
   - 使用 Apify 抓取 profile 数据
   - 获取最近的帖子和互动数据
   - 提取联系信息

4. **AI 深度分析**
   - Profile Summary（博主概况）
   - Audience Analysis（受众分析）
   - Collaboration Opportunities（合作机会）
   - 自动分类和打标签

5. **向量化搜索**
   - 基于语义的相似度搜索
   - Pinecone 向量数据库
   - 智能排序和推荐

6. **数据持久化**
   - SQLite 作为单一数据源
   - Pinecone 作为搜索索引
   - 智能同步机制

### 使用场景

- **品牌营销**: 寻找符合品牌调性的影响者
- **产品推广**: 找到目标受众匹配的创作者
- **市场调研**: 了解行业内的关键意见领袖
- **竞品分析**: 研究竞争对手合作的影响者

---

## 核心流程

### 完整工作流

```
1. 用户输入描述
   "fitness influencers in Singapore"
   ↓
2. Intent Analysis (LLM)
   提取：行业=fitness, 地点=Singapore, 约束=[]
   ↓
3. Google Dork Generation (LLM)
   生成："site:instagram.com fitness Singapore"
   ↓
4. Google Search (Apify)
   返回：30-50 个 Instagram profile URLs
   ↓
5. Instagram Scraping (Apify)
   抓取每个 profile：
   - 基础信息（followers, bio, etc.）
   - 最近 12 个帖子
   - 互动数据（likes, comments, views）
   ↓
6. LLM Analysis (并行处理)
   对每个 profile：
   - Profile Summary
   - Audience Analysis
   - Collaboration Opportunities
   - Category & Tags
   ↓
7. Save to SQLite (单一数据源)
   存储完整数据到数据库
   ↓
8. Vectorize & Upsert to Pinecone
   - 将 profile_summary 转为向量
   - 存储到 Pinecone（仅用于搜索）
   ↓
9. Vector Search
   基于用户描述查找相似 profiles
   返回：handles + scores
   ↓
10. Fetch from SQLite
    通过 handles 获取完整数据
    ↓
11. Return Results
    按相关性排序返回给前端
```

### 数据流优化

#### 核心原则：SQLite 为主，Pinecone 为辅

```
SQLite (Single Source of Truth)
   ↓ 单向同步
Pinecone (Search Index Only)
   ↓ 返回 handle + score
SQLite (查询完整数据)
   ↓
返回给前端
```

**关键点**：
- ✅ SQLite 是唯一的数据源
- ✅ Pinecone 只用于向量搜索
- ✅ 所有数据写入先到 SQLite
- ✅ 所有数据读取从 SQLite
- ❌ 永远不要从 Pinecone metadata 创建/更新数据

---

## 技术架构

### 技术栈

**后端**:
- FastAPI 0.115.0 (API 服务器)
- SQLAlchemy 2.0.34 (ORM)
- SQLite (数据库)
- Celery 5.4.0 (异步任务)
- Redis 5.0.8 (任务队列)

**前端**:
- Next.js 14 (React 框架)
- TypeScript
- Tailwind CSS

**外部服务**:
- **Apify**: 数据抓取
  - Google Search Actor
  - Instagram Profile Scraper
- **Pinecone**: 向量搜索
  - Inference API (内置 embedding)
- **Gemini/OpenAI**: LLM 服务
  - 意图分析
  - 内容生成
  - 分类标签

**LangChain 集成** (可选):
- 统一的 LLM chains
- Prompt 模板化管理
- 可通过配置开关启用

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │    Search    │  │   Results    │  │   Profile     │ │
│  │    Input     │  │    List      │  │   Detail      │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │              API Routes Layer                     │  │
│  │  /requests  /results  /influencers               │  │
│  └─────────────┬────────────────────────────────────┘  │
│                │                                         │
│  ┌─────────────▼──────────┬─────────────┬────────────┐ │
│  │  Discovery Manager     │  Pipeline   │  Search    │ │
│  │  - Request management  │  - Execute  │  - Vector  │ │
│  │  - Result storage      │  - Analyze  │  - Rank    │ │
│  │  - Status tracking     │  - Save     │  - Filter  │ │
│  └────────────────────────┴─────────────┴────────────┘ │
│                │                │              │         │
│  ┌─────────────▼────────────────▼──────────────▼─────┐ │
│  │    LLM Services         Apify Provider            │ │
│  │  - Intent parsing    - Google search              │ │
│  │  - Dork generation   - IG scraping                │ │
│  │  - Profile analysis  - Data extraction            │ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬─────────────┐
        │               │               │             │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐ ┌────▼────┐
│   Apify      │ │  Pinecone │ │   Gemini    │ │ SQLite  │
│   Actors     │ │  Vectors  │ │   API       │ │   DB    │
└──────────────┘ └───────────┘ └─────────────┘ └─────────┘
```

### 并发处理

```
Pipeline Run
    ↓
┌───┴────────────────────────────────┐
│ 发现阶段（串行）                    │
│ 1. Google Search                    │
│ 2. Instagram Scraping               │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ 分析阶段（并行）                    │
│ Profile 1 → LLM Analysis            │
│ Profile 2 → LLM Analysis            │
│ Profile 3 → LLM Analysis            │
│ ...                                 │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ 存储阶段（批量）                    │
│ 1. Batch save to SQLite             │
│ 2. Batch upsert to Pinecone         │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ 搜索阶段                            │
│ 1. Vector search                    │
│ 2. Fetch from SQLite                │
│ 3. Rank & return                    │
└─────────────────────────────────────┘
```

---

## 数据模型

### 数据库表结构

#### 1. `influencers` - 影响者主表

```sql
CREATE TABLE influencers (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE NOT NULL,           -- Instagram handle (@username)
    name TEXT,
    bio TEXT,
    profile_summary TEXT,                  -- LLM 生成的概况
    category TEXT,                         -- 分类
    tags TEXT,                             -- 标签（JSON array）
    
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
    post_sharing_percentage FLOAT,         -- 分享帖子占比
    post_collaboration_percentage FLOAT,   -- 合作帖子占比
    
    -- LLM 分析结果
    audience_analysis TEXT,                -- 受众分析
    collaboration_opportunity TEXT,        -- 合作机会
    
    -- 联系信息
    email TEXT,
    external_url TEXT,
    
    -- 元数据
    platform TEXT DEFAULT 'instagram',
    country TEXT,
    gender TEXT,
    profile_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_influencers_handle ON influencers(handle);
CREATE INDEX idx_influencers_category ON influencers(category);
CREATE INDEX idx_influencers_followers ON influencers(followers);
```

#### 2. `requests` - 搜索请求表

```sql
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,                  -- PARTIAL, PROCESSING, DONE, FAILED
    description TEXT NOT NULL,             -- 用户输入描述
    constraints TEXT,                      -- 约束条件
    intent TEXT,                           -- LLM 解析的意图
    query_embedding TEXT                   -- 查询向量（用于搜索）
);

CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at);
```

#### 3. `request_results` - 搜索结果关联表

```sql
CREATE TABLE request_results (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL,
    influencer_id INTEGER NOT NULL,
    score FLOAT,                           -- 来自 Pinecone 的相似度分数
    rank INTEGER,                          -- 排名
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
    FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE
);

CREATE INDEX idx_request_results_request_id ON request_results(request_id);
CREATE INDEX idx_request_results_score ON request_results(score);
```

### 状态枚举

#### Request 状态

- `PARTIAL` - 创建但未开始处理
- `PROCESSING` - 正在处理中
- `DONE` - 完成
- `FAILED` - 失败

### Pinecone 向量结构

```python
# Pinecone 中存储的向量记录
{
    "id": "instagram_username",           # 使用 handle 作为 ID
    "values": [0.1, 0.2, ...],           # 向量（由 Pinecone Inference 生成）
    "metadata": {
        "handle": "username",
        "platform": "instagram",
        "followers": 50000,
        "category": "fitness"
    }
}
```

**重要**：metadata 仅用于过滤和返回基本信息，不用于创建/更新数据库记录。

---

## 数据同步策略

### 核心原则

**SQLite 是唯一真相源 (Single Source of Truth)**

1. ✅ 所有数据先写入 SQLite
2. ✅ 再同步到 Pinecone（仅用于搜索）
3. ✅ 搜索时从 Pinecone 获取 handles + scores
4. ✅ 再从 SQLite 查询完整数据
5. ❌ 永远不要从 Pinecone 创建/更新 Influencer

### 数据流

#### 写入流程

```python
def save_and_sync(candidate_data):
    # Step 1: 保存到 SQLite（主数据源）
    influencer = Influencer(**candidate_data)
    db.add(influencer)
    db.commit()
    
    # Step 2: 同步到 Pinecone（搜索索引）
    vector_store.upsert_texts(
        texts=[influencer.profile_summary],
        ids=[f"instagram_{influencer.handle}"],
        metadatas=[{
            "handle": influencer.handle,
            "platform": "instagram",
            "followers": influencer.followers,
            "category": influencer.category
        }]
    )
    
    return influencer
```

#### 搜索流程

```python
def search_and_fetch(query: str, top_k: int = 20):
    # Step 1: 向量搜索（Pinecone）
    matches = vector_store.search_text(query, top_k=top_k)
    # matches = [
    #     {"id": "instagram_user1", "score": 0.95, "metadata": {...}},
    #     {"id": "instagram_user2", "score": 0.89, "metadata": {...}}
    # ]
    
    # Step 2: 提取 handles
    handles = [m["metadata"]["handle"] for m in matches]
    
    # Step 3: 从 SQLite 查询完整数据
    influencers = db.query(Influencer).filter(
        Influencer.handle.in_(handles)
    ).all()
    
    # Step 4: 合并 score 并排序
    handle_to_influencer = {inf.handle: inf for inf in influencers}
    results = []
    for match in matches:
        handle = match["metadata"]["handle"]
        if handle in handle_to_influencer:
            influencer = handle_to_influencer[handle]
            results.append({
                "influencer": influencer,
                "score": match["score"]
            })
    
    return results
```

#### 存储结果流程

```python
def store_results(request_id: int, matches: List[Dict]):
    """
    只存储引用关系，不创建新的 Influencer
    """
    for rank, match in enumerate(matches, 1):
        handle = match["metadata"]["handle"]
        
        # 从 SQLite 查找 Influencer
        influencer = db.query(Influencer).filter(
            Influencer.handle == handle
        ).first()
        
        if not influencer:
            # ❌ 不要创建！只记录警告
            logger.warning(
                f"Influencer @{handle} found in Pinecone but not in SQLite. "
                "Data inconsistency detected. Skipping."
            )
            continue
        
        # ✅ 只存储引用
        result = RequestResult(
            request_id=request_id,
            influencer_id=influencer.id,  # 来自 SQLite
            score=match.get("score"),      # 来自 Pinecone
            rank=rank
        )
        db.add(result)
    
    db.commit()
```

### 历史问题与解决

#### 问题 1：数据不一致

**场景 A**:
```
1. Pipeline 发现新博主 → 存入 SQLite ✅
2. Pipeline 向量化 → 存入 Pinecone ✅
3. 后来手动更新 SQLite 中的数据
   ❌ Pinecone 没有更新 → 不一致
```

**场景 B**:
```
1. Pinecone 中有旧数据
2. SQLite 中是空的或旧的
3. 搜索时从 Pinecone 返回
   ❌ SQLite 中找不到或数据不完整
```

#### 问题 2：职责不清晰

```
❌ Pinecone 既是搜索引擎，又是数据源
❌ SQLite 既是数据库，又依赖 Pinecone 补充
```

#### 解决方案

**1. 修改 `_store_results` 方法**

之前（错误）：
```python
if not influencer:
    # 从 Pinecone metadata 创建 Influencer ❌
    influencer = Influencer(
        profile_summary=meta.get("profile_summary"),
        ...
    )
```

现在（正确）：
```python
if not influencer:
    # 不创建！只记录警告 ✅
    logger.warning(
        f"Influencer @{handle} found in Pinecone but not in SQLite. "
        "Data inconsistency detected. Skipping."
    )
    continue

# 只存储引用（handle -> score mapping）
result = RequestResult(
    request_id=request.id,
    influencer_id=influencer.id,  # 来自 SQLite
    score=match.get("score"),      # 来自 Pinecone
    rank=rank,
)
```

**2. Pipeline 确保先写 SQLite**

```python
def run(self, description: str, constraints: str):
    # 1️⃣ 发现候选者
    candidates = self._discover(...)
    
    # 2️⃣ 先存入 SQLite（单一真相源）
    for candidate in candidates:
        influencer = self._save_to_database(db, candidate)
    
    # 3️⃣ 再同步到 Pinecone
    self._upsert_vectors(candidates)
    
    # 4️⃣ 搜索只返回 handle + score
    matches = self.vector_store.search_text(query, top_k=20)
    
    # 5️⃣ 存储结果引用
    self._store_results(db, request, matches)
```

**3. 数据更新策略**

如果需要更新数据，必须同时更新：
```python
# 1. 更新 SQLite
influencer.profile_summary = new_summary
db.commit()

# 2. 更新 Pinecone
vector_store.upsert_texts(
    texts=[new_summary],
    ids=[f"instagram_{influencer.handle}"],
    metadatas=[{...}]
)
```

### 数据一致性检查

提供工具脚本检查同步状态：

```bash
# 检查 SQLite 中有但 Pinecone 没有的
python scripts/sync_sqlite_to_pinecone.py

# 检查 Pinecone 中有但 SQLite 没有的
python scripts/sync_pinecone_to_sqlite.py

# 对比并同步
python scripts/sync_all.py
```

---

## 前端设计

### UI 布局

```
┌────────────────────────────────────────────────────────────────┐
│  Top Bar: Logo, Navigation                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Search Section                                         │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │ 描述你的需求...                                  │ │   │
│  │  │ "fitness influencers in Singapore"               │ │   │
│  │  └──────────────────────────────────────────────────┘ │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │ 约束条件（可选）...                              │ │   │
│  │  │ "must have > 10k followers"                      │ │   │
│  │  └──────────────────────────────────────────────────┘ │   │
│  │  [Search]                                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Status: Processing... (30% complete)                  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Results Grid (3 columns on desktop, 1 on mobile)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ [Avatar] │  │ [Avatar] │  │ [Avatar] │                    │
│  │ @user1   │  │ @user2   │  │ @user3   │                    │
│  │ 50k fol. │  │ 120k fol.│  │ 30k fol. │                    │
│  │ Fitness  │  │ Lifestyle│  │ Health   │                    │
│  │ 95% match│  │ 89% match│  │ 87% match│                    │
│  │ [View]   │  │ [View]   │  │ [View]   │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Profile Detail Modal

```
┌────────────────────────────────────────────────────────────────┐
│  @username                                        [✕]           │
├────────────────────────────────────────────────────────────────┤
│  ┌────────┐  Name: John Doe                                    │
│  │        │  Followers: 50,000                                 │
│  │ Avatar │  Avg Likes: 2,500                                  │
│  │        │  Category: Fitness                                 │
│  └────────┘  📧 email@example.com                              │
│              🔗 website.com                                     │
├────────────────────────────────────────────────────────────────┤
│  📝 Profile Summary                                            │
│  A fitness coach based in Singapore...                         │
│                                                                  │
│  👥 Audience Analysis                                          │
│  Primary audience: 25-35 year old professionals...            │
│                                                                  │
│  🤝 Collaboration Opportunities                                │
│  - Product reviews                                              │
│  - Sponsored posts                                              │
│  - Long-term ambassador                                         │
│                                                                  │
│  [Visit Instagram] [Save for Later]                           │
└────────────────────────────────────────────────────────────────┘
```

### 响应式设计

- **桌面**: 3列网格，详细展示
- **平板**: 2列网格
- **手机**: 单列列表，卡片式展示

---

## 后端服务

### 1. Discovery Manager (发现管理器)

**职责**: 协调整个发现流程

**核心方法**:

```python
class DiscoveryManager:
    def create_request(
        self, 
        description: str, 
        constraints: str = None
    ) -> Request:
        """
        创建新的搜索请求
        
        流程:
        1. 创建 Request 记录（status=PARTIAL）
        2. 触发异步任务
        3. 返回 Request ID
        """
    
    def get_request(self, request_id: int) -> Request:
        """
        获取请求状态
        
        返回:
        - status: PARTIAL/PROCESSING/DONE/FAILED
        - created_at
        - intent（如果已解析）
        """
    
    def get_results(
        self, 
        request_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取搜索结果
        
        流程:
        1. 查询 request_results 表
        2. JOIN influencers 表
        3. 按 score 降序排序
        4. 分页返回
        
        返回:
        [{
            "influencer": {...},  # 完整数据
            "score": 0.95,        # 相似度
            "rank": 1
        }]
        """
```

### 2. Discovery Pipeline (发现流程)

**职责**: 执行发现和分析流程

**核心方法**:

```python
class DiscoveryPipeline:
    def run(
        self, 
        request_id: int,
        description: str,
        constraints: str = None
    ):
        """
        完整的发现流程
        
        步骤:
        1. Intent Analysis
        2. Google Dork Generation
        3. Google Search
        4. Instagram Scraping
        5. LLM Analysis (并行)
        6. Save to SQLite
        7. Upsert to Pinecone
        8. Vector Search
        9. Store Results
        """
    
    def _discover(self, intent: Dict) -> List[Dict]:
        """
        发现阶段
        
        流程:
        1. 生成 Google Dork
        2. 执行 Google 搜索
        3. 抓取 Instagram profiles
        
        返回: 候选人列表
        """
    
    def _analyze(self, candidates: List[Dict]) -> List[Dict]:
        """
        分析阶段
        
        并行处理每个候选人:
        1. Profile Summary
        2. Audience Analysis
        3. Collaboration Opportunities
        4. Category & Tags
        
        返回: 带分析结果的候选人列表
        """
    
    def _save_to_database(
        self, 
        db: Session, 
        candidate: Dict
    ) -> Influencer:
        """
        保存到 SQLite
        
        处理:
        - 去重（基于 handle）
        - 如果存在则更新
        - 如果不存在则创建
        """
    
    def _upsert_vectors(self, candidates: List[Dict]):
        """
        同步到 Pinecone
        
        批量上传:
        - texts: profile_summary
        - ids: instagram_handle
        - metadatas: 基本信息
        """
```

### 3. Search Service (搜索服务)

**职责**: 向量搜索和排序

**核心方法**:

```python
class SearchService:
    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Dict = None
    ) -> List[Dict]:
        """
        语义搜索
        
        流程:
        1. 向量搜索（Pinecone）
        2. 应用过滤器（category, followers 等）
        3. 从 SQLite 获取完整数据
        4. 合并 score
        5. 排序返回
        
        返回:
        [{
            "influencer": Influencer object,
            "score": 0.95
        }]
        """
```

### 4. LLM Services (LLM 服务)

**职责**: 各种 AI 分析任务

```python
class IntentParser:
    def parse(self, description: str, constraints: str) -> Dict:
        """
        解析用户意图
        
        输入: "fitness influencers in Singapore"
        输出: {
            "industry": "fitness",
            "location": "Singapore",
            "constraints": []
        }
        """

class GoogleDorkGenerator:
    def generate(self, intent: Dict) -> str:
        """
        生成 Google Dork
        
        输入: {"industry": "fitness", "location": "Singapore"}
        输出: "site:instagram.com fitness Singapore"
        """

class ProfileSummaryGenerator:
    def generate(self, profile_data: Dict) -> str:
        """
        生成 Profile Summary
        
        输入: IG profile + posts 数据
        输出: 简洁的概况文本（2-3 句话）
        """

class AudienceAnalyzer:
    def analyze(self, profile_data: Dict, summary: str) -> str:
        """
        分析受众
        
        输入: profile 数据 + summary
        输出: 受众分析（年龄、性别、兴趣等）
        """

class CollaborationAnalyzer:
    def analyze(self, profile_data: Dict, summary: str) -> str:
        """
        分析合作机会
        
        输入: profile 数据 + summary
        输出: 推荐的合作方式
        """
```

### 5. Apify Provider (数据抓取)

**职责**: 封装 Apify API

```python
class ApifyProvider:
    def search_google(
        self,
        query: str,
        max_results: int = 50
    ) -> List[str]:
        """
        Google 搜索
        
        使用 Apify Google Search Actor
        返回: Instagram profile URLs 列表
        """
    
    def scrape_instagram_profile(
        self,
        username: str
    ) -> Dict:
        """
        抓取 Instagram profile
        
        使用 Apify Instagram Profile Scraper
        返回: {
            "handle": "username",
            "followers": 50000,
            "bio": "...",
            "posts": [...]  # 最近 12 个帖子
        }
        """
```

---

## API 参考

### 请求管理

#### POST `/api/v1/requests`
创建新的搜索请求

**Request**:
```json
{
  "description": "fitness influencers in Singapore",
  "constraints": "must have > 10k followers"
}
```

**Response**:
```json
{
  "id": 1,
  "status": "PARTIAL",
  "created_at": "2026-01-21T10:00:00"
}
```

#### GET `/api/v1/requests/{id}`
获取请求状态

**Response**:
```json
{
  "id": 1,
  "status": "PROCESSING",  // PARTIAL, PROCESSING, DONE, FAILED
  "description": "fitness influencers in Singapore",
  "intent": {
    "industry": "fitness",
    "location": "Singapore"
  },
  "created_at": "2026-01-21T10:00:00"
}
```

#### GET `/api/v1/requests/{id}/results`
获取搜索结果

**Query Parameters**:
- `limit`: 默认 20
- `offset`: 默认 0

**Response**:
```json
{
  "request_id": 1,
  "total_results": 50,
  "results": [
    {
      "influencer": {
        "id": 1,
        "handle": "fitness_sg",
        "name": "John Doe",
        "followers": 50000,
        "profile_summary": "...",
        "audience_analysis": "...",
        "collaboration_opportunity": "..."
      },
      "score": 0.95,
      "rank": 1
    }
  ]
}
```

### 影响者管理

#### GET `/api/v1/influencers`
列出所有影响者

**Query Parameters**:
- `category`: 过滤分类
- `min_followers`: 最小粉丝数
- `limit`: 默认 50
- `offset`: 默认 0

#### GET `/api/v1/influencers/{id}`
获取单个影响者详情

#### POST `/api/v1/influencers/{id}/update`
手动更新影响者数据

---

## 配置说明

### 环境变量

`backend/.env`:

```env
# ==== LLM 配置 ====
LLM_PROVIDER=gemini                    # gemini 或 openai
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp

# ==== Pinecone 配置 ====
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=moreach
PINECONE_HOST=your-index-host.pinecone.io

# ==== Apify 配置 ====
APIFY_TOKEN=your_apify_token

# Apify Actors (可选，有默认值)
APIFY_GOOGLE_SEARCH_ACTOR=apify~google-search-scraper
APIFY_INSTAGRAM_SCRAPER_ACTOR=apify~instagram-profile-scraper

# ==== 数据库 ====
DATABASE_URL=sqlite:///./app.db

# ==== Redis (Celery) ====
REDIS_URL=redis://localhost:6379/0

# ==== LangChain (可选) ====
USE_LANGCHAIN_CHAINS=true              # 启用 LangChain
USE_LANGCHAIN_EMBEDDINGS=false         # 保持 false
USE_LANGCHAIN_VECTORSTORE=false        # 保持 false
```

### Pinecone 配置

**Index 设置**:
- Dimensions: 根据 embedding model（通常 1024 或 1536）
- Metric: cosine
- Pod Type: p1.x1 或更高

**Inference API** (推荐):
```python
# 使用 Pinecone 内置 embedding
vector_store.upsert_texts(
    texts=["text content"],
    inference=True  # 自动 embedding
)
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

# Terminal 3: Frontend
cd frontend
npm run dev
```

#### 2. 创建搜索请求

**方式 1: 通过前端**
1. 访问 http://localhost:3000/try
2. 输入描述："fitness influencers in Singapore"
3. 可选：添加约束
4. 点击 "Search"
5. 等待结果（5-10分钟）

**方式 2: 通过 API**
```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{
    "description": "fitness influencers in Singapore",
    "constraints": "must have > 10k followers"
  }'
```

#### 3. 查看结果

```bash
# 检查状态
curl http://localhost:8000/api/v1/requests/1

# 获取结果
curl http://localhost:8000/api/v1/requests/1/results
```

### 工作流示例

#### 场景：寻找健身影响者

```python
# 1. 创建请求
response = requests.post(
    "http://localhost:8000/api/v1/requests",
    json={
        "description": "fitness influencers in Singapore with focus on yoga",
        "constraints": "female, 20k-100k followers, high engagement"
    }
)
request_id = response.json()["id"]

# 2. 轮询状态
import time
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/requests/{request_id}"
    )
    status = status_response.json()["status"]
    
    if status == "DONE":
        break
    elif status == "FAILED":
        print("Search failed!")
        exit(1)
    
    print(f"Status: {status}, waiting...")
    time.sleep(30)

# 3. 获取结果
results_response = requests.get(
    f"http://localhost:8000/api/v1/requests/{request_id}/results"
)
results = results_response.json()["results"]

# 4. 处理结果
for result in results[:5]:  # Top 5
    influencer = result["influencer"]
    score = result["score"]
    
    print(f"@{influencer['handle']} - {score*100:.1f}% match")
    print(f"Followers: {influencer['followers']:,}")
    print(f"Summary: {influencer['profile_summary']}")
    print(f"Email: {influencer.get('email', 'N/A')}")
    print("---")
```

---

## 最佳实践

### 搜索描述优化

**好的描述**:
```
✅ "fitness influencers in Singapore focusing on yoga and wellness"
✅ "tech reviewers who cover smartphones and gadgets, based in US"
✅ "fashion bloggers in Europe with minimalist aesthetic"
```

**不好的描述**:
```
❌ "influencers"（太泛）
❌ "best fitness people"（太主观）
❌ "找一些博主"（太模糊）
```

### 约束条件建议

**有效约束**:
- 粉丝数范围："10k-50k followers"
- 互动率："high engagement rate"
- 性别/年龄："female, 25-35 years old"
- 地理位置："based in Singapore"
- 内容类型："focus on product reviews"

### 性能优化

**1. 批量处理**
- 一次搜索可以发现 30-50 个 profiles
- 避免频繁的小请求

**2. 缓存利用**
- 已抓取的 profile 会保存在数据库
- 相似搜索会复用已有数据

**3. 并行分析**
- LLM 分析自动并行处理
- 加快整体流程

### 成本控制

**Apify 使用**:
- Google Search: ~$0.001/搜索
- Instagram Scraping: ~$0.01/profile
- 总成本: ~$0.50-1.00/搜索（30-50 profiles）

**LLM 使用**:
- Intent Analysis: 1 次
- Dork Generation: 1 次
- Profile Analysis: 3 次/profile × 50 profiles = 150 次
- 使用 Gemini Flash 可大幅降低成本

**Pinecone 使用**:
- 使用 Inference API 节省 embedding 成本
- 按需索引，不存储冗余数据

---

## 故障排查

### 问题：搜索一直是 PROCESSING 状态

**可能原因**:
1. Celery worker 未运行
2. Apify 配额不足
3. LLM API 限流
4. 网络问题

**排查步骤**:
```bash
# 1. 检查 Celery worker 日志
tail -f celery_worker.log

# 2. 检查 Apify 配额
# 访问 https://console.apify.com/account/usage

# 3. 测试 LLM API
python -c "from app.services.llm.client import LLMClient; \
            print(LLMClient().analyze('test'))"

# 4. 手动触发任务
python -c "from app.workers.tasks import run_discovery_pipeline; \
            run_discovery_pipeline.apply(args=(1,))"
```

### 问题：搜索结果为空

**可能原因**:
1. Google 搜索未找到相关 profiles
2. Instagram 抓取失败
3. Pinecone 搜索未匹配

**排查步骤**:
```bash
# 1. 检查 Request 的 intent
curl http://localhost:8000/api/v1/requests/1 | jq '.intent'

# 2. 检查数据库中是否有 influencers
sqlite3 app.db "SELECT COUNT(*) FROM influencers;"

# 3. 检查 Pinecone 中的向量数量
python scripts/debug_pinecone_search.py

# 4. 手动测试搜索
curl http://localhost:8000/api/v1/influencers?limit=10
```

### 问题：数据不一致（SQLite vs Pinecone）

**排查**:
```bash
# 检查同步状态
python scripts/sync_check.py

# 从 SQLite 同步到 Pinecone
python scripts/sync_sqlite_to_pinecone.py

# 从 Pinecone 同步到 SQLite（谨慎使用）
python scripts/sync_pinecone_to_sqlite.py
```

### 问题：LangChain 启用后出错

**排查**:
```bash
# 1. 确认依赖已安装
pip install -r requirements.txt

# 2. 检查配置
grep USE_LANGCHAIN backend/.env

# 3. 测试 LangChain
python -m app.services.langchain_poc.test_llm_chain

# 4. 如果失败，回滚
# 编辑 .env: USE_LANGCHAIN_CHAINS=false
```

---

## 技术参考

### 代码结构

```
backend/app/
├── api/v1/routes.py              # API 端点
├── models/
│   ├── tables.py                 # 数据库模型
│   └── schemas.py                # Pydantic schemas
├── providers/
│   ├── apify/client.py          # Apify 封装
│   ├── google/search.py         # Google 搜索
│   └── instagram/scrape.py      # IG 抓取
├── services/
│   ├── discovery/
│   │   ├── manager.py           # 主协调器
│   │   ├── pipeline.py          # 发现流程
│   │   └── search.py            # 向量搜索
│   ├── llm/                     # LLM 服务
│   │   ├── intent.py
│   │   ├── dork.py
│   │   ├── profile_summary.py
│   │   ├── audience_analysis.py
│   │   └── collaboration_analysis.py
│   ├── langchain/               # LangChain 集成（可选）
│   │   ├── config.py
│   │   ├── prompts/
│   │   └── chains/
│   └── vector/
│       └── pinecone.py          # Pinecone 客户端
└── workers/
    ├── celery_app.py            # Celery 配置
    └── tasks.py                 # 异步任务

frontend/app/
├── try/page.tsx                 # 搜索页面
├── lib/
│   ├── api.ts                   # API 调用
│   └── types.ts                 # TypeScript 类型
└── components/                  # UI 组件
```

### 关键文件

**后端**:
- `backend/app/services/discovery/manager.py` - 主要业务逻辑
- `backend/app/services/discovery/pipeline.py` - 发现流程实现
- `backend/app/api/v1/routes.py` - API 端点定义
- `backend/app/providers/apify/client.py` - Apify 集成

**前端**:
- `frontend/app/try/page.tsx` - 搜索界面

---

## 相关文档

- [README.md](README.md) - 项目概览
- [ARCHITECTURE.md](ARCHITECTURE.md) - 完整架构文档
- [REDDIT_DESIGN.md](REDDIT_DESIGN.md) - Reddit 功能设计
- [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) - LangChain 使用指南

---

## 结语

Instagram Influencer Discovery 是一个成熟的、生产就绪的系统，采用清晰的数据架构和智能的 AI 分析。

### 核心优势

✅ **AI 驱动** - 全流程智能化  
✅ **数据一致性** - SQLite 单一数据源  
✅ **高效搜索** - 向量化语义搜索  
✅ **可扩展** - 清晰的代码结构  
✅ **成本优化** - 批量处理和缓存  

### 开始使用

1. 配置 Apify、Pinecone 和 Gemini API
2. 启动所有服务
3. 创建第一个搜索请求
4. 查看和分析结果

祝你找到完美的影响者合作伙伴！🚀

---

**文档版本**: 1.0  
**最后更新**: 2026-01-21  
**维护者**: AI Assistant

