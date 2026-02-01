# Moreach System Architecture Documentation

> **Complete System Architecture Description**
>
> Includes Instagram Influencer Discovery and Reddit Lead Generation core features

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Instagram Influencer Discovery](#instagram-influencer-discovery)
3. [Reddit Lead Generation](#reddit-lead-generation)
4. [Data Architecture](#data-architecture)
5. [Technology Stack](#technology-stack)

---

## System Overview

### Core Features

Moreach is an AI-powered marketing tool platform that provides:

1. **Instagram Influencer Discovery**
   - Google Search + Instagram scraping
   - LLM analysis and ranking
   - Vector search (Pinecone)
   - SQLite data storage

2. **Reddit Lead Generation**
   - AI-driven subreddit discovery
   - Centralized dedup polling
   - Cost-optimized lead scoring
   - Auto-generated reply suggestions

### Technical Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js)                  │
│  • User Interface                                │
│  • API Calls                                     │
└─────────────────────────────────────────────────┘
                      ↓ HTTP
┌─────────────────────────────────────────────────┐
│          Backend API (FastAPI)                   │
│  • REST API Endpoints                            │
│  • Business Logic Layer                          │
└─────────────────────────────────────────────────┘
                      ↓
┌──────────┬──────────┬──────────┬──────────┐
│ Services │ Providers│ Workers  │ Models   │
└──────────┴──────────┴──────────┴──────────┘
     ↓          ↓          ↓          ↓
┌─────────────────────────────────────────────────┐
│  External Services                               │
│  • SQLite (Local Database)                       │
│  • Pinecone (Vector Search)                      │
│  • Gemini/OpenAI (LLM)                          │
│  • Reddit API (Social Data)                      │
│  • Apify (Instagram/Google)                      │
│  • Redis (Task Queue)                            │
└─────────────────────────────────────────────────┘
```

---

## Instagram Influencer Discovery

### Core Architecture

Instagram Influencer Discovery system uses **SQLite as primary, Pinecone as secondary** data architecture:

```
User Input → Intent Analysis → Google Dork → Google Search
    ↓
Instagram Scraping → LLM Analysis → SQLite (Primary Data Source)
    ↓                                    ↓
Vector Search ← Pinecone (Search Index) ← Sync
    ↓
Return Results ← SQLite (Complete Data)
```

**Core Principles**:
- SQLite is the Single Source of Truth
- Pinecone is only used for vector search
- Write to SQLite first, then sync to Pinecone
- Search returns handles, then query complete data from SQLite

### Main Services

```
backend/app/services/discovery/
├── manager.py       # Coordinator: request management, result storage
├── pipeline.py      # Pipeline: discover → analyze → store → search
└── search.py        # Vector search and ranking

backend/app/services/llm/
├── intent.py        # Intent analysis
├── dork.py          # Google Dork generation
├── profile_*.py     # Profile analysis (summary, audience, collaboration)

backend/app/providers/
├── apify/           # Data scraping
├── google/          # Google search
└── instagram/       # Instagram scraping
```

**Detailed Design**: See [IG_DESIGN.md](IG_DESIGN.md)

---

## Reddit Lead Generation

### Core Architecture

Reddit Lead Generation system uses **centralized dedup polling** and **cost-optimized funnel** design:

```
Business Description → AI Generate Query → Discover Subreddits → User Selection
    ↓
Celery Beat (every 6h) → Centralized Polling → Dedup Scraping
    ↓
Keyword Filter (free, 70-90% filter) → LLM Analysis (paid)
    ↓
Create Leads → Distribute to All Related Campaigns
    ↓
User Views → AI Suggested Reply → Interaction Marking
```

**Core Principles**:
- Centralized Polling: Multiple campaigns share the same subreddit, only scrape once
- Cost Optimization: Keyword filter first (free), then LLM analysis (paid), saves 80% cost
- Save First Score Later: Data safety, score each and commit immediately
- Discrete Score Tiers: 100/80/70/60/50/0, generous standards

### Main Services

```
backend/app/services/reddit/
├── discovery.py      # Subreddit discovery and ranking
├── polling.py        # Centralized dedup polling
└── scoring.py        # Two-stage cost-optimized scoring

backend/app/providers/reddit/
└── apify.py          # Apify Reddit Scraper
    ├── Community Search Actor
    └── Reddit Scraper Actor

backend/app/workers/
├── celery_app.py     # Scheduled task configuration
└── tasks.py          # poll_reddit_leads task
```

**Detailed Design**: See [REDDIT_DESIGN.md](REDDIT_DESIGN.md)

---

## Data Architecture

### Instagram Influencer Data

```sql
-- Main table: Influencers
CREATE TABLE influencers (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE,
    name TEXT,
    bio TEXT,
    profile_summary TEXT,        -- LLM generated
    category TEXT,
    tags TEXT,

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
    post_sharing_percentage FLOAT,
    post_collaboration_percentage FLOAT,

    -- LLM analysis
    audience_analysis TEXT,
    collaboration_opportunity TEXT,

    -- Contact info
    email TEXT,
    external_url TEXT,

    -- Other
    platform TEXT,
    country TEXT,
    gender TEXT,
    profile_url TEXT,
    created_at DATETIME
);

-- Search requests
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    created_at DATETIME,
    status TEXT,  -- PARTIAL, PROCESSING, DONE, FAILED
    description TEXT,
    constraints TEXT,
    intent TEXT,
    query_embedding TEXT
);

-- Request results (references)
CREATE TABLE request_results (
    id INTEGER PRIMARY KEY,
    request_id INTEGER,
    influencer_id INTEGER,
    score FLOAT,     -- from Pinecone
    rank INTEGER,
    FOREIGN KEY (request_id) REFERENCES requests(id),
    FOREIGN KEY (influencer_id) REFERENCES influencers(id)
);
```

### Reddit Lead Data

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

-- Leads
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

    -- AI analysis
    relevancy_score FLOAT,
    relevancy_reason TEXT,
    suggested_comment TEXT,
    suggested_dm TEXT,

    status TEXT,  -- NEW, REVIEWED, CONTACTED, DISMISSED
    discovered_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (campaign_id) REFERENCES reddit_campaigns(id)
);

-- Global polling tracking
CREATE TABLE global_subreddit_polls (
    id INTEGER PRIMARY KEY,
    subreddit_name TEXT UNIQUE,
    last_poll_at DATETIME,
    last_post_timestamp FLOAT,
    poll_count INTEGER,
    total_posts_found INTEGER
);
```

### Data Relationships

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

global_subreddit_polls (independent tracking)
```

---

## Technology Stack

### Backend

- **Framework**: FastAPI 0.115.0
- **Database**: SQLite (SQLAlchemy 2.0.34)
- **Task Queue**: Celery 5.4.0 + Redis 5.0.8
- **Vector DB**: Pinecone
- **LLM**: Gemini (google-genai 0.7.0) / OpenAI

### External Services

- **Apify**: Instagram scraping, Google search
- **Pinecone**: Vector search
- **Gemini/OpenAI**: LLM analysis

### Frontend

- **Framework**: Next.js
- **Styling**: Tailwind CSS
- **Language**: TypeScript

### Development Tools

- **API Client**: httpx 0.27.2
- **Environment**: python-dotenv 1.0.1
- **Validation**: pydantic 2.8.2

---

## Deployment Architecture

### Development Environment

```
Terminal 1: FastAPI Server
python -m app.main

Terminal 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

Terminal 3: Celery Beat (Scheduled Tasks)
celery -A app.workers.celery_app beat --loglevel=info

Terminal 4: Redis
redis-server

Frontend:
cd frontend && npm run dev
```

### Production Environment (Recommended)

```
┌─────────────────────────────────────────┐
│         Nginx (Reverse Proxy)            │
└─────────────────────────────────────────┘
           │
           ├─ /api → FastAPI (Gunicorn)
           └─ / → Next.js (Static Files)

FastAPI → Celery Workers (Multi-process)
       → Celery Beat (Single Process)
       → Redis
       → SQLite / PostgreSQL
```

**Service Configuration**:
- **FastAPI**: Gunicorn + Uvicorn workers
- **Celery**: 4-8 workers
- **Redis**: Persistence configuration
- **Database**: Upgrade to PostgreSQL (recommended for production)

---

## Performance Considerations

### Instagram Discovery

- **Google Search**: ~10 seconds/query
- **Instagram Scraping**: ~5 seconds/profile
- **LLM Analysis**: ~2 seconds/profile
- **Total Time**: ~30-50 profiles takes 5-10 minutes

**Optimization Suggestions**:
- Parallel processing of multiple profiles
- Cache Google search results
- Batch LLM requests

### Reddit Polling

- **Subreddit Poll**: ~10 seconds/subreddit
- **Keyword Filter**: Instant (<0.1 seconds/post)
- **LLM Analysis**: ~1-2 seconds/post
- **Total Time**: 100 subreddits ~20 minutes

**Optimization Suggestions**:
- Adjust polling frequency (default 6 hours)
- Increase keyword filter threshold (reduce LLM calls)
- Use faster LLM (Gemini Flash)

---

## Security Considerations

### API Keys

- All keys stored in `.env` file
- `.env` is in `.gitignore`
- Never hardcode keys

### Rate Limiting

- **Reddit API**: 100 requests/minute (built-in limit)
- **Apify**: Based on plan
- **Gemini**: 60 requests/minute (free tier)

### Data Privacy

- Only store public data
- Comply with Reddit/Instagram ToS
- No user password storage

---

## Monitoring & Logging

### Log Levels

```python
# Development
logging.basicConfig(level=logging.DEBUG)

# Production
logging.basicConfig(level=logging.INFO)
```

### Key Metrics

**Instagram**:
- Search request count
- Discovered influencers count
- LLM call count
- Error rate

**Reddit**:
- Active campaign count
- Polling cycle time
- Lead generation count
- LLM cost

### Error Tracking

```python
# In code
try:
    result = risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
    # Optional: send to Sentry or similar service
```

---

## Summary

### Architecture Principles

1. **Single Source of Truth**: SQLite is the only truth for all data
2. **Separation of Concerns**: Pinecone only does search, not storage
3. **Cost Optimization**: Multi-stage filtering reduces LLM calls
4. **Scalability**: Centralized dedup polling
5. **Data Consistency**: Write SQLite first, then sync Pinecone

### Best Practices

1. **Never** create/update Influencer from Pinecone metadata
2. **Always** write SQLite first, then Pinecone
3. **Always** read complete data from SQLite
4. **Regularly** check SQLite ↔ Pinecone consistency
5. **Monitor** LLM call costs

---

## Related Documentation

- [README.md](README.md) - Project overview and quick start
- [IG_DESIGN.md](IG_DESIGN.md) - Instagram feature complete documentation
- [REDDIT_DESIGN.md](REDDIT_DESIGN.md) - Reddit feature complete documentation
- [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) - LangChain usage guide

---

**Document Version**: 2.0
**Last Updated**: 2026-01-31
**Changes**: Converted to English, streamlined architecture documentation
