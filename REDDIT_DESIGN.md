# Reddit Lead Generation - Complete Design Document

> **AI-Powered Reddit Lead Generation System**
>
> Automatically discover, monitor, and score potential customer opportunities from Reddit discussions

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Workflow](#core-workflow)
3. [Technical Architecture](#technical-architecture)
4. [Data Model](#data-model)
5. [Frontend Design](#frontend-design)
6. [Backend Services](#backend-services)
7. [Scoring System](#scoring-system)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Usage Guide](#usage-guide)
11. [Optimization History](#optimization-history)

---

## System Overview

### Core Features

**Reddit Lead Generation** is an automated lead mining system that discovers and evaluates potential customers from Reddit discussions using AI technology.

#### Key Features

1. **Intelligent Subreddit Discovery**
   - LLM automatically generates search queries
   - Finds relevant communities based on business description
   - AI scores subreddit relevance to business (0-100 points)

2. **Automated Monitoring**
   - Automatically fetches new posts every 6 hours
   - Deduplication mechanism prevents duplicate fetching
   - Only fetches new content after specified time

3. **AI Scoring System**
   - Uses discrete scoring tiers (100/80/70/60/50/0)
   - Lenient scoring criteria (50+ points if there's any relevance)
   - Each result is immediately written to database

4. **AI-Generated Responses**
   - Automatically generates Suggested Comment
   - Automatically generates Suggested DM
   - Provides relevance reasoning

5. **Manual Operation Workflow**
   - One-click copy + redirect to Reddit
   - Auto-marks as Commented/DMed
   - Clean state management with no residual state

### Use Cases

- **B2B SaaS Customer Acquisition**: Discover users discussing problems your product solves in relevant communities
- **Product Validation**: Understand real needs and pain points of target users
- **Competitive Research**: Discover user feedback and needs regarding competitors
- **Community Building**: Find potential early users and advocates

---

## Core Workflow

### Complete Workflow

```
1. User describes business
   ↓
2. AI generates search keywords
   ↓
3. Call Apify to search subreddits (batch)
   ↓
4. Use LLM to score each subreddit (0-1)
   - Relevance score: 70%
   - Activity score: 30% (based on subscriber count)
   ↓
5. User selects subreddits to monitor
   ↓
6. Runs automatically every 6 hours (or manual trigger):
   - Fetch 20 new posts/subreddit
   - Save to database first (relevancy_score = None)
   - Then call LLM to score each one
   - Immediately commit each result
   - Delete posts below 50 points
   ↓
7. Frontend display (Inbox style):
   - Inbox: New leads
   - Commented: Already commented
   - DMed: Already messaged
   ↓
8. User actions:
   - Copy & comment manually → Copy + redirect to post + mark Commented
   - Copy & DM manually → Copy + redirect to user page + mark DMed
```

### Data Flow Optimizations

#### Optimization 1: Batch Subreddit Search

**Before**: Each keyword called Apify separately
```python
for query in ["SaaS", "startups", "business"]:
    results = search_communities(query)  # 3 API calls
```

**Now**: Single call with all keywords
```python
results = search_communities(["SaaS", "startups", "business"])  # 1 API call
```

#### Optimization 2: Save First, Score Later

**Before**: Scoring failure caused data loss
```python
for post in posts:
    score = llm_score(post)  # ❌ If fails, all previous posts are lost
    save(post, score)
```

**Now**: Save immediately, then score asynchronously
```python
# Step 1: Save all posts
for post in posts:
    save(post, relevancy_score=None)  # ✅ Data is safe
db.commit()

# Step 2: Score each and commit immediately
for lead in leads:
    score = llm_score(lead)
    lead.relevancy_score = score
    db.commit()  # ✅ Each result saved immediately
```

---

## Technical Architecture

### Tech Stack

**Backend**:
- FastAPI (API server)
- SQLAlchemy (ORM)
- SQLite (Database)
- Celery (Scheduled tasks)
- Redis (Celery broker)

**Frontend**:
- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS

**External Services**:
- **Apify** (Data scraping)
  - Community Search Actor: Search subreddits
  - Reddit Scraper Actor: Fetch posts
- **Gemini API** (LLM service)
  - Generate search queries
  - Score subreddit relevance
  - Score post relevance
  - Generate suggested responses

### System Architecture Diagram

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

### Celery Scheduled Tasks

```
Celery Beat (Scheduler)
    ↓ Every 6 hours
┌───▼─────────────────────────────┐
│  poll_reddit_leads Task          │
│  1. Get all ACTIVE campaigns    │
│  2. Collect deduplicated subreddits │
│  3. For each subreddit:         │
│     - Fetch 20 new posts        │
│     - Save to database          │
│     - LLM score each one        │
│     - Commit immediately        │
│  4. Delete low-score posts (< 50) │
└──────────────────────────────────┘
```

---

## Data Model

### Database Table Structure

#### 1. `reddit_campaigns` - Campaign Management

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

#### 2. `reddit_campaign_subreddits` - Subreddit Selection

```sql
CREATE TABLE reddit_campaign_subreddits (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    subreddit_name VARCHAR(128),
    subreddit_title VARCHAR(512),
    subreddit_description TEXT,
    subscribers INTEGER,
    relevance_score FLOAT,  -- LLM score 0.0-1.0
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    FOREIGN KEY(campaign_id) REFERENCES reddit_campaigns(id)
);
```

#### 3. `reddit_leads` - Lead Records

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
    relevancy_score FLOAT,  -- Can be NULL (pending) or 0-100
    relevancy_reason TEXT,
    suggested_comment TEXT,
    suggested_dm TEXT,
    status TEXT,  -- NEW, REVIEWED, CONTACTED, DISMISSED
    discovered_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(campaign_id) REFERENCES reddit_campaigns(id)
);
```

### Status Enumerations

#### Campaign Status

- `DISCOVERING` - Currently finding subreddits
- `ACTIVE` - Currently monitoring leads
- `PAUSED` - Temporarily stopped
- `COMPLETED` - Marked as complete by user

#### Lead Status

- `NEW` - New lead (Inbox)
- `REVIEWED` - Already commented (Commented)
- `CONTACTED` - Already messaged (DMed)
- `DISMISSED` - Ignored

**Note**: Frontend display to database mapping:
- Inbox → NEW
- Commented → REVIEWED
- DMed → CONTACTED

---

## Frontend Design

### UI Layout (Inbox Style)

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

### Adjustable Width

The right detail panel uses **golden ratio** (61.8% : 38.2%):
- Detail panel: 61.8% width (wider for easier reading)
- List panel: 38.2% width (compact preview)
- Users can drag boundaries to adjust
- Ratio automatically recalculates on window resize

### State Management Optimizations

#### Issue: State Residue on Tab Switch

**Cause**:
```typescript
// ❌ Wrong approach
setFilterStatus(status);  // Async update
handleViewLeads(campaign);  // Uses old filterStatus
```

**Solution**:
```typescript
// ✅ Correct approach
setFilterStatus(status);
await handleViewLeads(campaign, status);  // Pass new status directly
```

#### Optimization: Immediate UI Update

```typescript
async function handleCopyAndComment(lead) {
  await navigator.clipboard.writeText(lead.suggested_comment);
  await handleUpdateStatus(lead.id, "REVIEWED");

  // ✅ Immediately remove from list (no need to wait for API)
  setLeads(prev => prev.filter(l => l.id !== lead.id));
  setSelectedLead(leads.find(l => l.id !== lead.id));

  window.open(lead.post_url, '_blank');
}
```

### Frontend Compatibility

**Score Display** - Supports both formats:
```typescript
// Compatible with old format (0.0-1.0) and new format (0-100)
const score = lead.relevancy_score || 0;
const display = score <= 1 ? Math.round(score * 100) : Math.round(score);
// 0.72 → 72%
// 80 → 80%
```

---

## Backend Services

### 1. Discovery Service

**Responsibility**: Discover and score subreddits

**Core Methods**:

```python
class RedditDiscoveryService:
    def generate_search_queries(business_description: str) -> List[str]:
        """
        Use LLM to generate 5-8 search queries

        Input: "I sell project management SaaS for small teams"
        Output: ["project management", "productivity", "SaaS", "small teams"]
        """

    def discover_subreddits(search_queries: List[str]) -> List[Dict]:
        """
        Batch search subreddits (single Apify call)

        Input: ["SaaS", "startups", "business"]
        Output: [
            {name: "SaaS", subscribers: 50000, ...},
            {name: "startups", subscribers: 800000, ...}
        ]
        """

    def rank_subreddits(subreddits: List[Dict], business_desc: str) -> List[Dict]:
        """
        Use LLM to score subreddit relevance

        - Score range: 0.0-1.0 (decimal)
        - Composite score: 70% relevance + 30% activity
        - Activity based on logarithmic normalization of subscriber count

        Output: Sorted by composite_score in descending order
        """
```

### 2. Polling Service

**Responsibility**: Periodically fetch new posts

**Core Methods**:

```python
class RedditPollingService:
    def poll_campaign_immediately(campaign_id: int) -> Dict:
        """
        Immediately poll a campaign

        Process:
        1. Get all subreddits for the campaign
        2. Fetch 20 posts for each subreddit
        3. Save to database first
        4. LLM score each one
        5. Delete low-score posts
        """

    def poll_subreddit(subreddit_name: str, limit: int = 20) -> List[Dict]:
        """
        Fetch new posts from a single subreddit

        - Use Apify Reddit Scraper
        - sort="new", time_filter="day"
        - Filter posts after last poll
        """

    def _distribute_leads_to_campaign(
        campaign_id: int,
        subreddit: str,
        posts: List[Dict]
    ) -> int:
        """
        Create leads for campaign

        Process:
        1. Check deduplication (reddit_post_id)
        2. Save lead (score=None)
        3. Commit
        4. Score each one
        5. Commit each result
        6. Delete those < 50 points
        """
```

### 3. Scoring Service

**Responsibility**: AI scoring of post relevance

**Scoring Tiers** (discrete values):
- **100 points**: Perfect match - User explicitly needs this solution
- **80 points**: Strong relevance - Highly relevant with clear pain points
- **70 points**: Good lead - Related to business with potential opportunity
- **60 points**: Medium lead - Some relevance, worth contacting
- **50 points**: Weak lead - Marginally related but has minimal connection
- **0 points**: Not a lead - Completely irrelevant or spam

**Core Methods**:

```python
class RedditScoringService:
    def score_post(post: Dict, business_description: str) -> Dict:
        """
        Complete scoring process

        Returns:
        {
            "relevancy_score": 80,  # Discrete tier
            "relevancy_reason": "...",
            "suggested_comment": "...",
            "suggested_dm": "..."
        }
        """

    def llm_analyze(post: Dict, business_desc: str) -> Tuple:
        """
        LLM deep analysis

        Prompt requirements:
        - Lenient scoring criteria
        - Only use specified tiers (100/80/70/60/50/0)
        - Give at least 50 points if there's any relevance

        Returns: (score, reason, comment, dm)
        """
```

**LLM Prompt Strategy**:

```
Scoring Guidelines:
- Be GENEROUS with scoring
- Give at least 50 points if there's any connection
- Only give 0 points if completely irrelevant
- If industry/topic is mentioned, at least 50-60 points
- If there's a clear problem to solve, 70+ points
- Reserve 100 points for posts explicitly seeking this solution
```

### 4. Apify Provider (Data Scraping)

**Responsibility**: Encapsulate Apify API calls

**Actors Used**:

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

**Field Mapping** (important):
```python
# Apify returned field names → Internal field names
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

## API Reference

### Campaign Management

#### POST `/api/v1/reddit/campaigns`
Create new campaign

**Request**:
```json
{
  "business_description": "I sell project management SaaS for small teams",
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
List all campaigns

#### GET `/api/v1/reddit/campaigns/{id}`
Get campaign details

#### POST `/api/v1/reddit/campaigns/{id}/pause`
Pause campaign

#### POST `/api/v1/reddit/campaigns/{id}/resume`
Resume campaign

### Subreddit Discovery

#### GET `/api/v1/reddit/campaigns/{id}/discover-subreddits`
Discover and score subreddits

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
Select subreddits and activate

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
Get campaign's subreddit list

### Leads Management

#### GET `/api/v1/reddit/campaigns/{id}/leads`
Get leads

**Query Parameters**:
- `status`: NEW/REVIEWED/CONTACTED/DISMISSED
- `limit`: Default 200
- `offset`: Default 0

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
Update lead status

**Request**:
```json
{
  "status": "REVIEWED"
}
```

### Operations

#### POST `/api/v1/reddit/campaigns/{id}/run-now`
Run campaign immediately (manual poll trigger)

#### POST `/api/v1/reddit/campaigns/{id}/rescore-leads`
Rescore unscored leads

---

## Configuration

### Environment Variables

`backend/.env`:

```env
# ==== Apify (required) ====
APIFY_TOKEN=your_apify_token_here

# Apify Actors (optional, have defaults)
APIFY_REDDIT_COMMUNITY_SEARCH_ACTOR=practicaltools~apify-reddit-api
APIFY_REDDIT_SCRAPER_ACTOR=harshmaur~reddit-scraper

# ==== LLM Configuration ====
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# ==== Database ====
DATABASE_URL=sqlite:///./app.db

# ==== Redis (Celery) ====
REDIS_URL=redis://localhost:6379/0
```

### Celery Scheduling

`backend/app/workers/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    "poll-reddit-leads": {
        "task": "app.workers.tasks.poll_reddit_leads",
        "schedule": 3600 * 6,  # Every 6 hours
    },
}
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

# Terminal 3: Celery Beat (Scheduled Tasks)
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 4: Frontend
cd frontend
npm run dev
```

#### 2. Create Campaign

1. Visit http://localhost:3000/reddit
2. Click "New Campaign"
3. Describe your business
4. AI generates search terms and discovers subreddits
5. Select relevant subreddits
6. Activate campaign

#### 3. View Leads

1. Wait for automatic polling (6 hours) or click "Run Now"
2. Click "View Leads"
3. View new leads in Inbox
4. Click a lead to view details
5. Copy suggested content and go to Reddit to engage

### Operation Workflow

#### Commented Flow

1. Select a lead in Inbox
2. Read Suggested Comment
3. Click **"Copy & comment manually"**
   - Comment copied to clipboard
   - Reddit post page opens
   - Lead marked as "Commented"
4. Paste and post comment on Reddit

#### DMed Flow

1. Select a lead in Inbox
2. Read Suggested DM
3. Click **"Copy & DM manually"**
   - DM copied to clipboard
   - Reddit user profile opens
   - Lead marked as "DMed"
4. Click "Send Message" and paste DM

---

## Optimization History

### 2026-01-21: Scoring System Refactor

**Problem**: All posts scored 0 points

**Cause**:
- Keyword filtering too strict
- Scoring system confusion (0-1 vs 0-100)
- Cached data on scoring failure

**Solution**:
1. **Changed to discrete tiers** (100/80/70/60/50/0)
2. **Lenient scoring criteria** - 50+ points if there's any relevance
3. **Immediate database writes** - Commit each result immediately
4. **Frontend compatibility for both formats** - Auto-detect and convert

### 2026-01-20: Subreddit Scoring

**Problem**: Subreddits had no relevance scores

**Solution**:
1. Added `relevance_score` field to database
2. LLM scoring for subreddits (0.0-1.0)
3. Composite score: 70% relevance + 30% activity
4. Sort by composite score

### 2026-01-19: Process Optimization

**Problem**:
- Each keyword called Apify separately (wasteful)
- Scoring failure caused data loss

**Solution**:
1. **Batch search**: Single API call with all keywords
2. **Save first, score later**:
   - Step 1: Save all posts (score=None)
   - Step 2: Score each and commit immediately

### 2026-01-18: Apify Migration

**Problem**: PRAW API unstable with limited functionality

**Solution**: Migrated to Apify
- Community Search Actor
- Reddit Scraper Actor
- More stable data scraping

### 2026-01-17: UI Refactor

**Problem**: List-style layout inefficient

**Solution**:
- Inbox-style three-column layout
- Golden ratio proportions
- Draggable width adjustment

### 2026-01-16: State Management Optimization

**Problem**: State residue on tab switch

**Solution**:
- Pass explicit status parameter
- Immediate UI update
- Reload data on each switch

---

## Best Practices

### Campaign Strategy

**Good business descriptions**:
```
✅ "I sell project management SaaS for teams of 5-20 people, focusing on agile development processes"
✅ "We help e-commerce sellers automate inventory management and order processing"
❌ "I sell software" (too vague)
❌ "The best project management tool" (too promotional)
```

**Subreddit selection**:
- Choose highly active ones (at least a few new posts per day)
- Target audience match
- Rules allow discussion of tools/solutions
- Don't select overly large general subreddits (like r/AskReddit)

### Engagement Tips

1. **Provide value first**: Help users, don't be too salesy
2. **Respond quickly**: Reddit moves fast, reply promptly
3. **Personalize content**: Use AI suggestions as a starting point, add personal touch
4. **Follow rules**: Read and follow each subreddit's rules
5. **Track results**: Record what works

### Cost Optimization

**Apify usage**:
- Only fetch 20 posts per subreddit
- Use time_filter to reduce useless data
- Batch search to avoid repeated calls

**LLM usage**:
- Save first, score later (avoid repeated fetching)
- Delete low-score posts (< 50)
- Use cheaper models (Gemini Flash)

---

## Troubleshooting

### Problem: No leads found

**Checklist**:
1. Is campaign status `ACTIVE`?
2. Is Celery Beat running?
3. Has it been more than 6 hours since last poll?
4. Does the subreddit have new posts?

**Manual trigger**:
```bash
# Method 1: API
curl -X POST http://localhost:8000/api/v1/reddit/campaigns/1/run-now

# Method 2: Python
python -c "from app.workers.tasks import poll_reddit_leads; poll_reddit_leads()"
```

### Problem: All posts score 0

**Possible causes**:
1. Using old scoring format (0-1)
2. LLM scoring failed

**Solution**:
```bash
# Rescore
curl -X POST http://localhost:8000/api/v1/reddit/campaigns/1/rescore-leads

# Or convert old data
sqlite3 app.db "UPDATE reddit_leads SET relevancy_score = relevancy_score * 100 WHERE relevancy_score <= 1;"
```

### Problem: Data incorrect after tab switch

**Cause**: State management bug (fixed)

**Verify fix**: Frontend code should have:
```typescript
await handleViewLeads(campaign, status);  // ✅ Pass explicit status
```

### Problem: Apify quota exceeded

**Solution**:
1. Check [Apify Console Usage](https://console.apify.com/organization/usage)
2. Upgrade plan or purchase more credits
3. Reduce polling frequency (increase hours)
4. Reduce number of posts fetched per poll

---

## Technical Reference

### Code Structure

```
backend/app/
├── api/v1/routes.py              # API endpoints
├── models/
│   ├── tables.py                 # Database models
│   └── schemas.py                # Pydantic schemas
├── providers/reddit/
│   └── apify.py                  # Apify wrapper
├── services/reddit/
│   ├── discovery.py              # Subreddit discovery
│   ├── polling.py                # Polling service
│   └── scoring.py                # Scoring service
├── services/llm/
│   └── client.py                 # LLM client
└── workers/
    ├── celery_app.py             # Celery configuration
    └── tasks.py                  # Background tasks

frontend/app/
├── reddit/page.tsx               # Reddit page
├── lib/
│   ├── api.ts                    # API calls
│   └── types.ts                  # TypeScript types
└── components/
    └── Navigation.tsx            # Navigation bar
```

### Key Files

**Backend**:
- `backend/app/api/v1/routes.py` (591 lines) - All API endpoints
- `backend/app/services/reddit/polling.py` (513 lines) - Polling logic
- `backend/app/services/reddit/scoring.py` (300 lines) - Scoring logic
- `backend/app/providers/reddit/apify.py` (424 lines) - Apify integration

**Frontend**:
- `frontend/app/reddit/page.tsx` (1000+ lines) - Complete UI

---

## Conclusion

Reddit Lead Generation is a complete, production-ready system that has undergone multiple optimizations and fixes.

### Core Advantages

- **AI-Powered** - Automatic discovery, scoring, and response generation
- **Cost-Optimized** - Save first then score, batch API calls
- **User-Friendly** - Inbox style, one-click operations
- **Stable and Reliable** - Comprehensive error handling and data protection
- **Highly Configurable** - Flexible scoring criteria and polling frequency

### Getting Started

1. Configure Apify and Gemini API
2. Start all services
3. Create your first campaign
4. Wait or manually trigger polling
5. View and process leads in Inbox

Good luck with your customer acquisition!

---

**Document Version**: 2.0
**Last Updated**: 2026-01-31
**Maintainer**: AI Assistant

