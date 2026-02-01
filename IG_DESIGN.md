# Instagram Influencer Discovery - Complete Design Document

> **AI-Powered Instagram Influencer Discovery System**
>
> Automatically discover, analyze, and recommend relevant influencers through Google Search and Instagram scraping

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Workflow](#core-workflow)
3. [Technical Architecture](#technical-architecture)
4. [Data Model](#data-model)
5. [Data Sync Strategy](#data-sync-strategy)
6. [Frontend Design](#frontend-design)
7. [Backend Services](#backend-services)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Usage Guide](#usage-guide)
11. [Best Practices](#best-practices)

---

## System Overview

### Core Features

**Instagram Influencer Discovery** is an intelligent influencer discovery system that automatically finds and analyzes influencers matching brand requirements using AI technology.

#### Main Features

1. **Intelligent Intent Analysis**
   - LLM parses user requirements
   - Extracts industry, location, and constraints
   - Generates optimized search strategies

2. **Google Dork Search**
   - AI generates precise search queries
   - Automatically finds Instagram profiles
   - Returns candidate list

3. **Instagram Data Scraping**
   - Uses Apify to scrape profile data
   - Retrieves recent posts and engagement data
   - Extracts contact information

4. **AI Deep Analysis**
   - Profile Summary (influencer overview)
   - Audience Analysis
   - Collaboration Opportunities
   - Automatic categorization and tagging

5. **Vector Search**
   - Semantic similarity-based search
   - Pinecone vector database
   - Intelligent ranking and recommendations

6. **Data Persistence**
   - SQLite as single source of truth
   - Pinecone as search index
   - Intelligent sync mechanism

### Use Cases

- **Brand Marketing**: Find influencers matching brand identity
- **Product Promotion**: Find creators with matching target audiences
- **Market Research**: Understand key opinion leaders in the industry
- **Competitive Analysis**: Research influencers collaborating with competitors

---

## Core Workflow

### Complete Workflow

```
1. User Input Description
   "fitness influencers in Singapore"
   ↓
2. Intent Analysis (LLM)
   Extract: industry=fitness, location=Singapore, constraints=[]
   ↓
3. Google Dork Generation (LLM)
   Generate: "site:instagram.com fitness Singapore"
   ↓
4. Google Search (Apify)
   Return: 30-50 Instagram profile URLs
   ↓
5. Instagram Scraping (Apify)
   Scrape each profile:
   - Basic info (followers, bio, etc.)
   - Latest 12 posts
   - Engagement data (likes, comments, views)
   ↓
6. LLM Analysis (parallel processing)
   For each profile:
   - Profile Summary
   - Audience Analysis
   - Collaboration Opportunities
   - Category & Tags
   ↓
7. Save to SQLite (single source of truth)
   Store complete data to database
   ↓
8. Vectorize & Upsert to Pinecone
   - Convert profile_summary to vector
   - Store in Pinecone (search only)
   ↓
9. Vector Search
   Find similar profiles based on user description
   Return: handles + scores
   ↓
10. Fetch from SQLite
    Get complete data via handles
    ↓
11. Return Results
    Return to frontend sorted by relevance
```

### Data Flow Optimization

#### Core Principle: SQLite Primary, Pinecone Secondary

```
SQLite (Single Source of Truth)
   ↓ One-way sync
Pinecone (Search Index Only)
   ↓ Returns handle + score
SQLite (Query complete data)
   ↓
Return to frontend
```

**Key Points**:
- SQLite is the only data source
- Pinecone is only used for vector search
- All data writes go to SQLite first
- All data reads come from SQLite
- Never create/update data from Pinecone metadata

---

## Technical Architecture

### Tech Stack

**Backend**:
- FastAPI 0.115.0 (API server)
- SQLAlchemy 2.0.34 (ORM)
- SQLite (database)
- Celery 5.4.0 (async tasks)
- Redis 5.0.8 (task queue)

**Frontend**:
- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS

**External Services**:
- **Apify**: Data scraping
  - Google Search Actor
  - Instagram Profile Scraper
- **Pinecone**: Vector search
  - Inference API (built-in embedding)
- **Gemini/OpenAI**: LLM services
  - Intent analysis
  - Content generation
  - Category tagging

**LangChain Integration** (optional):
- Unified LLM chains
- Prompt template management
- Can be enabled via configuration

### System Architecture Diagram

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

### Concurrent Processing

```
Pipeline Run
    ↓
┌───┴────────────────────────────────┐
│ Discovery Phase (sequential)        │
│ 1. Google Search                    │
│ 2. Instagram Scraping               │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ Analysis Phase (parallel)           │
│ Profile 1 → LLM Analysis            │
│ Profile 2 → LLM Analysis            │
│ Profile 3 → LLM Analysis            │
│ ...                                 │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ Storage Phase (batch)               │
│ 1. Batch save to SQLite             │
│ 2. Batch upsert to Pinecone         │
└────┬───────────────────────────────┘
     │
┌────▼───────────────────────────────┐
│ Search Phase                        │
│ 1. Vector search                    │
│ 2. Fetch from SQLite                │
│ 3. Rank & return                    │
└─────────────────────────────────────┘
```

---

## Data Model

### Database Table Structure

#### 1. `influencers` - Influencer Main Table

```sql
CREATE TABLE influencers (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE NOT NULL,           -- Instagram handle (@username)
    name TEXT,
    bio TEXT,
    profile_summary TEXT,                  -- LLM-generated summary
    category TEXT,                         -- Category
    tags TEXT,                             -- Tags (JSON array)

    -- Basic metrics
    followers FLOAT,
    avg_likes FLOAT,
    avg_comments FLOAT,
    avg_video_views FLOAT,

    -- Peak metrics
    highest_likes FLOAT,
    highest_comments FLOAT,
    highest_video_views FLOAT,

    -- Post analysis
    post_sharing_percentage FLOAT,         -- Sharing post percentage
    post_collaboration_percentage FLOAT,   -- Collaboration post percentage

    -- LLM analysis results
    audience_analysis TEXT,                -- Audience analysis
    collaboration_opportunity TEXT,        -- Collaboration opportunities

    -- Contact information
    email TEXT,
    external_url TEXT,

    -- Metadata
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

#### 2. `requests` - Search Request Table

```sql
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,                  -- PARTIAL, PROCESSING, DONE, FAILED
    description TEXT NOT NULL,             -- User input description
    constraints TEXT,                      -- Constraints
    intent TEXT,                           -- LLM-parsed intent
    query_embedding TEXT                   -- Query vector (for search)
);

CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at);
```

#### 3. `request_results` - Search Result Association Table

```sql
CREATE TABLE request_results (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL,
    influencer_id INTEGER NOT NULL,
    score FLOAT,                           -- Similarity score from Pinecone
    rank INTEGER,                          -- Ranking
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
    FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE
);

CREATE INDEX idx_request_results_request_id ON request_results(request_id);
CREATE INDEX idx_request_results_score ON request_results(score);
```

### Status Enums

#### Request Status

- `PARTIAL` - Created but not started processing
- `PROCESSING` - Currently processing
- `DONE` - Completed
- `FAILED` - Failed

### Pinecone Vector Structure

```python
# Vector record stored in Pinecone
{
    "id": "instagram_username",           # Use handle as ID
    "values": [0.1, 0.2, ...],           # Vector (generated by Pinecone Inference)
    "metadata": {
        "handle": "username",
        "platform": "instagram",
        "followers": 50000,
        "category": "fitness"
    }
}
```

**Important**: metadata is only used for filtering and returning basic info, not for creating/updating database records.

---

## Data Sync Strategy

### Core Principles

**SQLite is the Single Source of Truth**

1. All data is written to SQLite first
2. Then synced to Pinecone (for search only)
3. During search, get handles + scores from Pinecone
4. Then query complete data from SQLite
5. Never create/update Influencer from Pinecone

### Data Flow

#### Write Flow

```python
def save_and_sync(candidate_data):
    # Step 1: Save to SQLite (primary data source)
    influencer = Influencer(**candidate_data)
    db.add(influencer)
    db.commit()

    # Step 2: Sync to Pinecone (search index)
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

#### Search Flow

```python
def search_and_fetch(query: str, top_k: int = 20):
    # Step 1: Vector search (Pinecone)
    matches = vector_store.search_text(query, top_k=top_k)
    # matches = [
    #     {"id": "instagram_user1", "score": 0.95, "metadata": {...}},
    #     {"id": "instagram_user2", "score": 0.89, "metadata": {...}}
    # ]

    # Step 2: Extract handles
    handles = [m["metadata"]["handle"] for m in matches]

    # Step 3: Query complete data from SQLite
    influencers = db.query(Influencer).filter(
        Influencer.handle.in_(handles)
    ).all()

    # Step 4: Merge scores and sort
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

#### Store Results Flow

```python
def store_results(request_id: int, matches: List[Dict]):
    """
    Only store reference relationships, don't create new Influencers
    """
    for rank, match in enumerate(matches, 1):
        handle = match["metadata"]["handle"]

        # Find Influencer from SQLite
        influencer = db.query(Influencer).filter(
            Influencer.handle == handle
        ).first()

        if not influencer:
            # DON'T create! Only log warning
            logger.warning(
                f"Influencer @{handle} found in Pinecone but not in SQLite. "
                "Data inconsistency detected. Skipping."
            )
            continue

        # Only store reference
        result = RequestResult(
            request_id=request_id,
            influencer_id=influencer.id,  # From SQLite
            score=match.get("score"),      # From Pinecone
            rank=rank
        )
        db.add(result)

    db.commit()
```

### Historical Issues and Solutions

#### Issue 1: Data Inconsistency

**Scenario A**:
```
1. Pipeline discovers new influencer → Store in SQLite
2. Pipeline vectorizes → Store in Pinecone
3. Later manually update data in SQLite
   Pinecone not updated → Inconsistency
```

**Scenario B**:
```
1. Pinecone has old data
2. SQLite is empty or outdated
3. Search returns from Pinecone
   Can't find or incomplete data in SQLite
```

#### Issue 2: Unclear Responsibilities

```
Pinecone is both search engine and data source
SQLite is both database and depends on Pinecone for supplementation
```

#### Solution

**1. Modify `_store_results` Method**

Before (wrong):
```python
if not influencer:
    # Create Influencer from Pinecone metadata (WRONG)
    influencer = Influencer(
        profile_summary=meta.get("profile_summary"),
        ...
    )
```

Now (correct):
```python
if not influencer:
    # Don't create! Only log warning (CORRECT)
    logger.warning(
        f"Influencer @{handle} found in Pinecone but not in SQLite. "
        "Data inconsistency detected. Skipping."
    )
    continue

# Only store reference (handle -> score mapping)
result = RequestResult(
    request_id=request.id,
    influencer_id=influencer.id,  # From SQLite
    score=match.get("score"),      # From Pinecone
    rank=rank,
)
```

**2. Pipeline Ensures Writing to SQLite First**

```python
def run(self, description: str, constraints: str):
    # 1. Discover candidates
    candidates = self._discover(...)

    # 2. First save to SQLite (single source of truth)
    for candidate in candidates:
        influencer = self._save_to_database(db, candidate)

    # 3. Then sync to Pinecone
    self._upsert_vectors(candidates)

    # 4. Search only returns handle + score
    matches = self.vector_store.search_text(query, top_k=20)

    # 5. Store result references
    self._store_results(db, request, matches)
```

**3. Data Update Strategy**

When updating data, must update both:
```python
# 1. Update SQLite
influencer.profile_summary = new_summary
db.commit()

# 2. Update Pinecone
vector_store.upsert_texts(
    texts=[new_summary],
    ids=[f"instagram_{influencer.handle}"],
    metadatas=[{...}]
)
```

### Data Consistency Checks

Provide utility scripts to check sync status:

```bash
# Check records in SQLite but not in Pinecone
python scripts/sync_sqlite_to_pinecone.py

# Check records in Pinecone but not in SQLite
python scripts/sync_pinecone_to_sqlite.py

# Compare and sync
python scripts/sync_all.py
```

---

## Frontend Design

### UI Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Top Bar: Logo, Navigation                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Search Section                                         │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │ Describe your needs...                           │ │   │
│  │  │ "fitness influencers in Singapore"               │ │   │
│  │  └──────────────────────────────────────────────────┘ │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │ Constraints (optional)...                        │ │   │
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
│  @username                                        [X]           │
├────────────────────────────────────────────────────────────────┤
│  ┌────────┐  Name: John Doe                                    │
│  │        │  Followers: 50,000                                 │
│  │ Avatar │  Avg Likes: 2,500                                  │
│  │        │  Category: Fitness                                 │
│  └────────┘  Email: email@example.com                          │
│              Website: website.com                               │
├────────────────────────────────────────────────────────────────┤
│  Profile Summary                                                │
│  A fitness coach based in Singapore...                         │
│                                                                  │
│  Audience Analysis                                              │
│  Primary audience: 25-35 year old professionals...            │
│                                                                  │
│  Collaboration Opportunities                                    │
│  - Product reviews                                              │
│  - Sponsored posts                                              │
│  - Long-term ambassador                                         │
│                                                                  │
│  [Visit Instagram] [Save for Later]                           │
└────────────────────────────────────────────────────────────────┘
```

### Responsive Design

- **Desktop**: 3-column grid, detailed display
- **Tablet**: 2-column grid
- **Mobile**: Single-column list, card-style display

---

## Backend Services

### 1. Discovery Manager

**Responsibility**: Coordinate the entire discovery process

**Core Methods**:

```python
class DiscoveryManager:
    def create_request(
        self,
        description: str,
        constraints: str = None
    ) -> Request:
        """
        Create a new search request

        Flow:
        1. Create Request record (status=PARTIAL)
        2. Trigger async task
        3. Return Request ID
        """

    def get_request(self, request_id: int) -> Request:
        """
        Get request status

        Returns:
        - status: PARTIAL/PROCESSING/DONE/FAILED
        - created_at
        - intent (if parsed)
        """

    def get_results(
        self,
        request_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get search results

        Flow:
        1. Query request_results table
        2. JOIN influencers table
        3. Sort by score descending
        4. Return with pagination

        Returns:
        [{
            "influencer": {...},  # Complete data
            "score": 0.95,        # Similarity
            "rank": 1
        }]
        """
```

### 2. Discovery Pipeline

**Responsibility**: Execute discovery and analysis flow

**Core Methods**:

```python
class DiscoveryPipeline:
    def run(
        self,
        request_id: int,
        description: str,
        constraints: str = None
    ):
        """
        Complete discovery flow

        Steps:
        1. Intent Analysis
        2. Google Dork Generation
        3. Google Search
        4. Instagram Scraping
        5. LLM Analysis (parallel)
        6. Save to SQLite
        7. Upsert to Pinecone
        8. Vector Search
        9. Store Results
        """

    def _discover(self, intent: Dict) -> List[Dict]:
        """
        Discovery phase

        Flow:
        1. Generate Google Dork
        2. Execute Google search
        3. Scrape Instagram profiles

        Returns: Candidate list
        """

    def _analyze(self, candidates: List[Dict]) -> List[Dict]:
        """
        Analysis phase

        Parallel processing for each candidate:
        1. Profile Summary
        2. Audience Analysis
        3. Collaboration Opportunities
        4. Category & Tags

        Returns: Candidate list with analysis results
        """

    def _save_to_database(
        self,
        db: Session,
        candidate: Dict
    ) -> Influencer:
        """
        Save to SQLite

        Handling:
        - Deduplication (based on handle)
        - Update if exists
        - Create if not exists
        """

    def _upsert_vectors(self, candidates: List[Dict]):
        """
        Sync to Pinecone

        Batch upload:
        - texts: profile_summary
        - ids: instagram_handle
        - metadatas: Basic info
        """
```

### 3. Search Service

**Responsibility**: Vector search and ranking

**Core Methods**:

```python
class SearchService:
    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Semantic search

        Flow:
        1. Vector search (Pinecone)
        2. Apply filters (category, followers, etc.)
        3. Get complete data from SQLite
        4. Merge scores
        5. Sort and return

        Returns:
        [{
            "influencer": Influencer object,
            "score": 0.95
        }]
        """
```

### 4. LLM Services

**Responsibility**: Various AI analysis tasks

```python
class IntentParser:
    def parse(self, description: str, constraints: str) -> Dict:
        """
        Parse user intent

        Input: "fitness influencers in Singapore"
        Output: {
            "industry": "fitness",
            "location": "Singapore",
            "constraints": []
        }
        """

class GoogleDorkGenerator:
    def generate(self, intent: Dict) -> str:
        """
        Generate Google Dork

        Input: {"industry": "fitness", "location": "Singapore"}
        Output: "site:instagram.com fitness Singapore"
        """

class ProfileSummaryGenerator:
    def generate(self, profile_data: Dict) -> str:
        """
        Generate Profile Summary

        Input: IG profile + posts data
        Output: Concise summary text (2-3 sentences)
        """

class AudienceAnalyzer:
    def analyze(self, profile_data: Dict, summary: str) -> str:
        """
        Analyze audience

        Input: profile data + summary
        Output: Audience analysis (age, gender, interests, etc.)
        """

class CollaborationAnalyzer:
    def analyze(self, profile_data: Dict, summary: str) -> str:
        """
        Analyze collaboration opportunities

        Input: profile data + summary
        Output: Recommended collaboration methods
        """
```

### 5. Apify Provider

**Responsibility**: Encapsulate Apify API

```python
class ApifyProvider:
    def search_google(
        self,
        query: str,
        max_results: int = 50
    ) -> List[str]:
        """
        Google Search

        Uses Apify Google Search Actor
        Returns: List of Instagram profile URLs
        """

    def scrape_instagram_profile(
        self,
        username: str
    ) -> Dict:
        """
        Scrape Instagram profile

        Uses Apify Instagram Profile Scraper
        Returns: {
            "handle": "username",
            "followers": 50000,
            "bio": "...",
            "posts": [...]  # Latest 12 posts
        }
        """
```

---

## API Reference

### Request Management

#### POST `/api/v1/requests`
Create a new search request

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
Get request status

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
Get search results

**Query Parameters**:
- `limit`: Default 20
- `offset`: Default 0

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

### Influencer Management

#### GET `/api/v1/influencers`
List all influencers

**Query Parameters**:
- `category`: Filter by category
- `min_followers`: Minimum follower count
- `limit`: Default 50
- `offset`: Default 0

#### GET `/api/v1/influencers/{id}`
Get single influencer details

#### POST `/api/v1/influencers/{id}/update`
Manually update influencer data

---

## Configuration

### Environment Variables

`backend/.env`:

```env
# ==== LLM Configuration ====
LLM_PROVIDER=gemini                    # gemini or openai
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp

# ==== Pinecone Configuration ====
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=moreach
PINECONE_HOST=your-index-host.pinecone.io

# ==== Apify Configuration ====
APIFY_TOKEN=your_apify_token

# Apify Actors (optional, has defaults)
APIFY_GOOGLE_SEARCH_ACTOR=apify~google-search-scraper
APIFY_INSTAGRAM_SCRAPER_ACTOR=apify~instagram-profile-scraper

# ==== Database ====
DATABASE_URL=sqlite:///./app.db

# ==== Redis (Celery) ====
REDIS_URL=redis://localhost:6379/0

# ==== LangChain (optional) ====
USE_LANGCHAIN_CHAINS=true              # Enable LangChain
USE_LANGCHAIN_EMBEDDINGS=false         # Keep false
USE_LANGCHAIN_VECTORSTORE=false        # Keep false
```

### Pinecone Configuration

**Index Settings**:
- Dimensions: Based on embedding model (usually 1024 or 1536)
- Metric: cosine
- Pod Type: p1.x1 or higher

**Inference API** (recommended):
```python
# Use Pinecone built-in embedding
vector_store.upsert_texts(
    texts=["text content"],
    inference=True  # Auto embedding
)
```

---

## Usage Guide

### Quick Start

#### 1. Start Services

```bash
# Terminal 1: API Server
cd backend
python -m app.main

# Terminal 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
```

#### 2. Create Search Request

**Method 1: Via Frontend**
1. Visit http://localhost:3000/try
2. Enter description: "fitness influencers in Singapore"
3. Optional: Add constraints
4. Click "Search"
5. Wait for results (5-10 minutes)

**Method 2: Via API**
```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{
    "description": "fitness influencers in Singapore",
    "constraints": "must have > 10k followers"
  }'
```

#### 3. View Results

```bash
# Check status
curl http://localhost:8000/api/v1/requests/1

# Get results
curl http://localhost:8000/api/v1/requests/1/results
```

### Workflow Example

#### Scenario: Finding Fitness Influencers

```python
# 1. Create request
response = requests.post(
    "http://localhost:8000/api/v1/requests",
    json={
        "description": "fitness influencers in Singapore with focus on yoga",
        "constraints": "female, 20k-100k followers, high engagement"
    }
)
request_id = response.json()["id"]

# 2. Poll status
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

# 3. Get results
results_response = requests.get(
    f"http://localhost:8000/api/v1/requests/{request_id}/results"
)
results = results_response.json()["results"]

# 4. Process results
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

## Best Practices

### Search Description Optimization

**Good descriptions**:
```
"fitness influencers in Singapore focusing on yoga and wellness"
"tech reviewers who cover smartphones and gadgets, based in US"
"fashion bloggers in Europe with minimalist aesthetic"
```

**Poor descriptions**:
```
"influencers" (too broad)
"best fitness people" (too subjective)
"find some bloggers" (too vague)
```

### Constraint Recommendations

**Effective constraints**:
- Follower range: "10k-50k followers"
- Engagement rate: "high engagement rate"
- Gender/age: "female, 25-35 years old"
- Geographic location: "based in Singapore"
- Content type: "focus on product reviews"

### Performance Optimization

**1. Batch Processing**
- A single search can discover 30-50 profiles
- Avoid frequent small requests

**2. Cache Utilization**
- Scraped profiles are saved in the database
- Similar searches will reuse existing data

**3. Parallel Analysis**
- LLM analysis automatically processes in parallel
- Speeds up overall flow

### Cost Control

**Apify Usage**:
- Google Search: ~$0.001/search
- Instagram Scraping: ~$0.01/profile
- Total cost: ~$0.50-1.00/search (30-50 profiles)

**LLM Usage**:
- Intent Analysis: 1 time
- Dork Generation: 1 time
- Profile Analysis: 3 times/profile x 50 profiles = 150 times
- Using Gemini Flash can significantly reduce costs

**Pinecone Usage**:
- Use Inference API to save embedding costs
- Index on demand, don't store redundant data

---

## Troubleshooting

### Issue: Search Stuck in PROCESSING Status

**Possible causes**:
1. Celery worker not running
2. Apify quota insufficient
3. LLM API rate limited
4. Network issues

**Troubleshooting steps**:
```bash
# 1. Check Celery worker logs
tail -f celery_worker.log

# 2. Check Apify quota
# Visit https://console.apify.com/account/usage

# 3. Test LLM API
python -c "from app.services.llm.client import LLMClient; \
            print(LLMClient().analyze('test'))"

# 4. Manually trigger task
python -c "from app.workers.tasks import run_discovery_pipeline; \
            run_discovery_pipeline.apply(args=(1,))"
```

### Issue: Empty Search Results

**Possible causes**:
1. Google search found no relevant profiles
2. Instagram scraping failed
3. Pinecone search didn't match

**Troubleshooting steps**:
```bash
# 1. Check Request intent
curl http://localhost:8000/api/v1/requests/1 | jq '.intent'

# 2. Check if database has influencers
sqlite3 app.db "SELECT COUNT(*) FROM influencers;"

# 3. Check vector count in Pinecone
python scripts/debug_pinecone_search.py

# 4. Test search manually
curl http://localhost:8000/api/v1/influencers?limit=10
```

### Issue: Data Inconsistency (SQLite vs Pinecone)

**Troubleshooting**:
```bash
# Check sync status
python scripts/sync_check.py

# Sync from SQLite to Pinecone
python scripts/sync_sqlite_to_pinecone.py

# Sync from Pinecone to SQLite (use with caution)
python scripts/sync_pinecone_to_sqlite.py
```

### Issue: Errors After Enabling LangChain

**Troubleshooting**:
```bash
# 1. Confirm dependencies installed
pip install -r requirements.txt

# 2. Check configuration
grep USE_LANGCHAIN backend/.env

# 3. Test LangChain
python -m app.services.langchain_poc.test_llm_chain

# 4. If failed, rollback
# Edit .env: USE_LANGCHAIN_CHAINS=false
```

---

## Technical Reference

### Code Structure

```
backend/app/
├── api/v1/routes.py              # API endpoints
├── models/
│   ├── tables.py                 # Database models
│   └── schemas.py                # Pydantic schemas
├── providers/
│   ├── apify/client.py          # Apify wrapper
│   ├── google/search.py         # Google search
│   └── instagram/scrape.py      # IG scraping
├── services/
│   ├── discovery/
│   │   ├── manager.py           # Main orchestrator
│   │   ├── pipeline.py          # Discovery flow
│   │   └── search.py            # Vector search
│   ├── llm/                     # LLM services
│   │   ├── intent.py
│   │   ├── dork.py
│   │   ├── profile_summary.py
│   │   ├── audience_analysis.py
│   │   └── collaboration_analysis.py
│   ├── langchain/               # LangChain integration (optional)
│   │   ├── config.py
│   │   ├── prompts/
│   │   └── chains/
│   └── vector/
│       └── pinecone.py          # Pinecone client
└── workers/
    ├── celery_app.py            # Celery configuration
    └── tasks.py                 # Async tasks

frontend/app/
├── try/page.tsx                 # Search page
├── lib/
│   ├── api.ts                   # API calls
│   └── types.ts                 # TypeScript types
└── components/                  # UI components
```

### Key Files

**Backend**:
- `backend/app/services/discovery/manager.py` - Main business logic
- `backend/app/services/discovery/pipeline.py` - Discovery flow implementation
- `backend/app/api/v1/routes.py` - API endpoint definitions
- `backend/app/providers/apify/client.py` - Apify integration

**Frontend**:
- `frontend/app/try/page.tsx` - Search interface

---

## Related Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture documentation
- [REDDIT_DESIGN.md](REDDIT_DESIGN.md) - Reddit feature design
- [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) - LangChain usage guide

---

## Conclusion

Instagram Influencer Discovery is a mature, production-ready system with clear data architecture and intelligent AI analysis.

### Core Advantages

- **AI-Driven** - Fully intelligent workflow
- **Data Consistency** - SQLite single source of truth
- **Efficient Search** - Vectorized semantic search
- **Extensible** - Clean code structure
- **Cost Optimized** - Batch processing and caching

### Getting Started

1. Configure Apify, Pinecone, and Gemini API
2. Start all services
3. Create your first search request
4. View and analyze results

Good luck finding your perfect influencer partners!

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
**Maintainer**: AI Assistant
