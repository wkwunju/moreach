# Moreach - AI-Powered Marketing Tool Platform

> **Intelligent Marketing Lead Discovery System**
>
> Instagram Influencer Discovery + Reddit Lead Generation

---

## Quick Navigation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[README.md](README.md)** | Project overview and quick start | First time exploring the project |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture overview | Understanding technical architecture and design principles |
| **[IG_DESIGN.md](IG_DESIGN.md)** | Instagram feature complete documentation | Using/developing Instagram features |
| **[REDDIT_DESIGN.md](REDDIT_DESIGN.md)** | Reddit feature complete documentation | Using/developing Reddit features |
| **[README_AUTH.md](README_AUTH.md)** | User authentication system | User registration and login functionality |
| **[LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md)** | LangChain usage guide | Enabling LangChain integration (optional) |

---

## Core Features

### 0. User Authentication System

Complete user registration and login system:
- Email/password authentication
- JWT Token management
- User profile collection (industry, job title, usage type)
- bcrypt password encryption
- Frontend and backend dual validation

**Complete Documentation**: [User Authentication System](README_AUTH.md)

### 1. Instagram Influencer Discovery

Automated influencer discovery workflow:
- Google Search + Instagram data scraping
- LLM-powered intelligent analysis (supports LangChain integration)
- Vector search (Pinecone)
- SQLite data storage

**Use Case**: Brands looking for suitable influencers for collaboration

### 2. Reddit Lead Generation

Intelligent B2B lead discovery:
- AI discovers relevant subreddits (using Apify Community Search)
- Automated monitoring and polling (using Apify Reddit Scraper)
- Cost-optimized scoring system (saves 80% LLM costs)
- Auto-generated reply suggestions (supports LangChain integration)

**Use Case**: B2B companies discovering potential customers from Reddit discussions

### 3. LangChain Integration

Optional LangChain integration for improved code quality and maintainability:
- All LLM services migrated to LangChain
- 60-70% code reduction
- Templated prompt management
- Unified chain interface
- Enable via config switch (`USE_LANGCHAIN_CHAINS=true`)
- Can rollback to original implementation anytime

**Details**: [LangChain Migration Guide](LANGCHAIN_MIGRATION_GUIDE.md)

---

## Technical Architecture

### System Architecture Diagram

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

### Shared Components

Both modules share the following core services:

| Service | Instagram Usage | Reddit Usage | Location |
|---------|-----------------|--------------|----------|
| **LLM Services** | Intent parsing, Profile analysis | Query generation, Post scoring | `services/llm/` |
| **Vector Store** | Profile embedding & search | (Not used) | `services/vector/` |
| **Apify Provider** | Google search, IG scraping | Community search, Reddit scraper | `providers/apify/` |
| **SQLite Database** | Influencers, Requests | Campaigns, Leads | `models/tables.py` |
| **Celery Workers** | Async discovery tasks | Scheduled polling (every 6h) | `workers/` |

### Data Isolation

- Instagram: `influencers`, `requests`, `request_results` tables
- Reddit: `reddit_campaigns`, `reddit_leads`, `reddit_campaign_subreddits` tables
- Completely independent, no cross-impact

**Detailed Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis
- API Keys:
  - Gemini or OpenAI
  - Apify (for Instagram and Reddit)
  - Pinecone

### 1. Clone the Project

```bash
git clone <repo-url>
cd moreach
```

### 2. Configure Environment Variables

Create `backend/.env` file:

```env
# LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=moreach
PINECONE_HOST=your_pinecone_host

# Apify (for Instagram and Reddit)
APIFY_TOKEN=your_apify_token

# Database & Redis
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0

# LangChain Integration (optional)
USE_LANGCHAIN_CHAINS=true       # Enable LangChain LLM chains
USE_LANGCHAIN_EMBEDDINGS=false  # Keep false (use Pinecone Inference)
USE_LANGCHAIN_VECTORSTORE=false # Keep false
```

### 3. Start Backend Services

```bash
# Terminal 1: API Server
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main

# Terminal 2: Celery Worker
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (Reddit auto-polling)
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 4: Redis
docker compose up -d
# Or use local Redis: redis-server
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

**Available Pages**:
- `/` - Homepage
- `/try` - Instagram Influencer Discovery
- `/reddit` - Reddit Lead Generation

---

## Complete Documentation

### Instagram Influencer Discovery

**Workflow**:
```
User input description
    ↓
LLM parses intent (shared LLM Service)
    ↓
Google Search (Apify Google Search Actor)
    ↓
Instagram Scraping (Apify IG Scraper)
    ↓
LLM Analysis (shared LLM Service)
    ├─ Profile Summary
    ├─ Audience Analysis
    └─ Collaboration Opportunities
    ↓
Store to SQLite (primary data source)
    ↓
Sync to Pinecone (vector index)
    ↓
Vector Search + Ranking
    ↓
Return Results
```

**API Endpoints**:
- `POST /api/v1/requests` - Create search request
- `GET /api/v1/requests/{id}` - Query request status
- `GET /api/v1/requests/{id}/results` - Get results

**Detailed Documentation**: See [IG_DESIGN.md](IG_DESIGN.md)

---

### Reddit Lead Generation

**Workflow**:
```
User describes business
    ↓
LLM generates search queries (shared LLM Service)
    ↓
Discover Subreddits (Apify Community Search)
    ↓
User selects subreddits
    ↓
Celery Beat triggers (every 6 hours)
    ↓
Centralized polling (Apify Reddit Scraper)
    └─ Dedup: Multiple campaigns share, only fetch once
    ↓
Save first, score later
    ├─ Save all posts to SQLite
    └─ Score each with LLM and commit immediately
    ↓
Distribute to all related campaigns
    ↓
User views Inbox
    ├─ AI suggested comment
    └─ AI suggested DM
    ↓
One-click copy + navigate + mark status
```

**API Endpoints**:
- `POST /api/v1/reddit/campaigns` - Create campaign
- `GET /api/v1/reddit/campaigns/{id}/discover-subreddits` - Discover subreddits
- `POST /api/v1/reddit/campaigns/{id}/select-subreddits` - Activate
- `GET /api/v1/reddit/campaigns/{id}/leads` - Get leads
- `POST /api/v1/reddit/campaigns/{id}/run-now` - Manual trigger polling

**Detailed Documentation**: See [REDDIT_DESIGN.md](REDDIT_DESIGN.md)

---

### Cross-Module Data Flow

#### LLM Service Calls

Both modules share the same LLM client and configuration:

```
Instagram                 Reddit
    ↓                       ↓
    └──── LLM Client ──────┘
           ↓
    LangChain (optional)
           ↓
    Gemini / OpenAI API
```

**Config Switches** (`backend/.env`):
- `USE_LANGCHAIN_CHAINS=true` - Both modules enable LangChain simultaneously
- `LLM_PROVIDER=gemini` - Both modules use the same LLM

#### Apify Service Calls

Both modules use different Apify Actors:

| Module | Actors | Usage |
|--------|--------|-------|
| **Instagram** | `google-search-scraper`<br>`instagram-profile-scraper` | Google search<br>IG data scraping |
| **Reddit** | `apify-reddit-api` (Community Search)<br>`reddit-scraper` | Subreddit search<br>Post scraping |

#### Database Structure

```sql
-- Instagram tables (independent)
influencers
requests
request_results

-- Reddit tables (independent)
reddit_campaigns
reddit_campaign_subreddits
reddit_leads
global_subreddit_polls

-- Completely isolated, no cross-impact
```

---

## Development Guide

### Project Structure

```
moreach/
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   │   ├── discovery/  # Instagram discovery
│   │   │   ├── reddit/     # Reddit leads
│   │   │   ├── llm/        # LLM services
│   │   │   └── vector/     # Vector search
│   │   ├── providers/      # External services
│   │   │   ├── apify/
│   │   │   ├── reddit/
│   │   │   └── instagram/
│   │   └── workers/        # Celery tasks
│   ├── scripts/           # Utility scripts
│   └── requirements.txt
│
├── frontend/
│   ├── app/               # Next.js pages
│   ├── components/        # React components
│   └── lib/              # Utilities
│
└── Documentation/
    ├── README.md          # This file
    ├── ARCHITECTURE.md    # Architecture docs
    ├── IG_DESIGN.md       # Instagram feature
    └── REDDIT_DESIGN.md   # Reddit feature
```

### Code Standards

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Frontend**: TypeScript, Next.js, Tailwind CSS
- **Style**: Follow PEP 8 (Python) and ESLint (TypeScript)

### Testing

```bash
# Backend tests
cd backend
python scripts/test_reddit_setup.py

# Frontend tests
cd frontend
npm test
```

---

## Performance Metrics

### Instagram Discovery

- **Search Time**: 5-10 minutes (30-50 profiles)
- **Accuracy**: High (LLM-driven analysis)
- **Cost**: Based on Apify and LLM usage

### Reddit Lead Generation

- **Polling Frequency**: Every 6 hours (configurable)
- **Cost**: ~$0.80/day/campaign (with keyword filtering)
- **vs No Filtering**: ~$4.00/day/campaign
- **Savings**: 80%

---

## Security & Privacy

- All API keys stored in environment variables
- Only public data collected
- Complies with Reddit/Instagram Terms of Service
- Built-in rate limiting

---

## Troubleshooting

### Common Issues

**Instagram discovery not working**:
- Check Apify token and quota
- Check Pinecone connection
- View Celery worker logs

**Reddit has no leads**:
- Confirm campaign status is ACTIVE
- Check if Celery Beat is running
- Wait for at least one polling cycle (6 hours)

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture overview, includes architecture design for both modules |
| [IG_DESIGN.md](IG_DESIGN.md) | Complete design documentation for Instagram influencer discovery |
| [REDDIT_DESIGN.md](REDDIT_DESIGN.md) | Complete design documentation for Reddit lead generation |
| [LANGCHAIN_MIGRATION_GUIDE.md](LANGCHAIN_MIGRATION_GUIDE.md) | LangChain integration usage guide |

---

## Contributing

Contributions are welcome! Please follow this process:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

[TBD]

---

## Acknowledgments

- Pinecone - Vector search
- Gemini - LLM services
- Apify - Data scraping

---

**Version**: 1.0.0
**Last Updated**: 2026-01-31
