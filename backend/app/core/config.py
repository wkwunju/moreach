from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "moreach-api"
    api_v1_prefix: str = "/api/v1"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-this-in-production-moreach-2024"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24  # Email verification token expires in 24 hours

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Email (SendGrid)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "hello@moreach.ai"
    FRONTEND_URL: str = "http://localhost:3000"

    database_url: str = "sqlite:///./app.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "gemini"
    dork_provider: str = "gemini"
    embedding_provider: str = "pinecone"
    
    # LangChain feature flags
    use_langchain_chains: bool = False  # LLM chains (intent, profile, etc.)
    use_langchain_embeddings: bool = False  # Embedding 层
    use_langchain_vectorstore: bool = False  # Vector store 层

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_dimensions: int = 1024

    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    pinecone_api_key: str = ""
    pinecone_index: str = "moreach"
    pinecone_host: str = ""
    pinecone_embedding_model: str = "llama-text-embed-v2"
    pinecone_namespace: str = ""

    apify_token: str = ""
    apify_google_actor: str = "apify/google-search-scraper"
    apify_instagram_actor: str = "apify/instagram-scraper"
    # Reddit actors - 使用您提供的 endpoint 格式
    # https://api.apify.com/v2/acts/practicaltools~apify-reddit-api/runs
    apify_reddit_community_search_actor: str = "practicaltools~apify-reddit-api"
    # https://api.apify.com/v2/acts/harshmaur~reddit-scraper/runs
    apify_reddit_scraper_actor: str = "harshmaur~reddit-scraper"

    # Reddit API Provider: "official" (Reddit API) or "rapidapi" (RapidAPI)
    reddit_api_provider: str = "official"

    # Official Reddit API
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "moreach:lead-gen:v1.0"

    # RapidAPI Reddit (Plan B)
    rapidapi_key: str = ""
    rapidapi_reddit_host: str = ""  # e.g., "reddit-scraper2.p.rapidapi.com"

    max_candidates: int = 40
    min_search_results: int = 8

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Stripe Price IDs (set these in .env)
    STRIPE_PRICE_STARTER_MONTHLY: str = ""
    STRIPE_PRICE_STARTER_ANNUALLY: str = ""
    STRIPE_PRICE_GROWTH_MONTHLY: str = ""
    STRIPE_PRICE_GROWTH_ANNUALLY: str = ""
    STRIPE_PRICE_PRO_MONTHLY: str = ""
    STRIPE_PRICE_PRO_ANNUALLY: str = ""

    # Admin users (bypass all subscription limits)
    ADMIN_USER_IDS: str = ""  # Comma-separated user IDs, e.g. "1,2"

    # Scheduled Polling Configuration
    # Enable/disable scheduled polling (set to False for local development)
    ENABLE_SCHEDULED_POLLING: bool = False

    # Poll times in UTC hours (comma-separated)
    # Starter plans: 2x/day - Europe morning (8am CET) and US West Coast morning (8am PST)
    POLL_TIMES_STARTER: str = "7,16"

    # Growth/Pro plans: 4x/day - more comprehensive coverage
    # UTC 07:00 = Europe 8am CET
    # UTC 11:00 = Europe afternoon, US East Coast morning
    # UTC 16:00 = US West Coast morning (8am PST)
    # UTC 22:00 = US afternoon, Asia morning
    POLL_TIMES_PREMIUM: str = "7,11,16,22"


settings = Settings()
