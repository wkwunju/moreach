import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Enum, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


# ======= User Authentication Models =======

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class IndustryType(str, enum.Enum):
    ECOMMERCE = "E-commerce"
    SAAS = "SaaS"
    AGENCY = "Marketing Agency"
    CONTENT_CREATOR = "Content Creator"
    RETAIL = "Retail"
    FASHION = "Fashion & Beauty"
    HEALTH_FITNESS = "Health & Fitness"
    FOOD_BEVERAGE = "Food & Beverage"
    TECH = "Technology"
    EDUCATION = "Education"
    OTHER = "Other"


class UsageType(str, enum.Enum):
    PERSONAL = "Personal Use"
    AGENCY = "Agency Use"
    TEAM = "Team Use"


class SubscriptionTier(str, enum.Enum):
    FREE_TRIAL = "FREE_TRIAL"
    # Legacy tiers (for backwards compatibility)
    MONTHLY = "MONTHLY"
    ANNUALLY = "ANNUALLY"
    # New tiered plans
    STARTER_MONTHLY = "STARTER_MONTHLY"
    STARTER_ANNUALLY = "STARTER_ANNUALLY"
    GROWTH_MONTHLY = "GROWTH_MONTHLY"
    GROWTH_ANNUALLY = "GROWTH_ANNUALLY"
    PRO_MONTHLY = "PRO_MONTHLY"
    PRO_ANNUALLY = "PRO_ANNUALLY"
    EXPIRED = "EXPIRED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Optional for OAuth users

    # OAuth providers
    google_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, unique=True, index=True)

    # Profile information
    full_name: Mapped[str] = mapped_column(String(256), default="")
    company: Mapped[str] = mapped_column(String(256), default="")
    job_title: Mapped[str] = mapped_column(String(256), default="")
    industry: Mapped[IndustryType] = mapped_column(Enum(IndustryType), default=IndustryType.OTHER)
    usage_type: Mapped[UsageType] = mapped_column(Enum(UsageType), default=UsageType.PERSONAL)
    
    # Account status
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # Block problematic users
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)  # For OAuth users to complete profile

    # Subscription
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.FREE_TRIAL)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Set to created_at + 7 days
    subscription_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Stripe
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, unique=True, index=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RequestStatus(str, enum.Enum):
    PARTIAL = "PARTIAL"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.PARTIAL)

    description: Mapped[str] = mapped_column(Text)
    constraints: Mapped[str] = mapped_column(Text, default="")
    intent: Mapped[str] = mapped_column(Text, default="")
    query_embedding: Mapped[str] = mapped_column(Text, default="")

    results = relationship("RequestResult", back_populates="request", cascade="all, delete-orphan")


class Influencer(Base):
    __tablename__ = "influencers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    handle: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    profile_summary: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(128), default="")
    tags: Mapped[str] = mapped_column(Text, default="")

    # Basic metrics
    followers: Mapped[float] = mapped_column(Float, default=0)
    avg_likes: Mapped[float] = mapped_column(Float, default=0)
    avg_comments: Mapped[float] = mapped_column(Float, default=0)
    avg_video_views: Mapped[float] = mapped_column(Float, default=0)
    
    # Peak performance metrics
    highest_likes: Mapped[float] = mapped_column(Float, default=0)
    highest_comments: Mapped[float] = mapped_column(Float, default=0)
    highest_video_views: Mapped[float] = mapped_column(Float, default=0)
    
    # Post analysis metrics
    post_sharing_percentage: Mapped[float] = mapped_column(Float, default=0)
    post_collaboration_percentage: Mapped[float] = mapped_column(Float, default=0)
    
    # Advanced analysis (LLM-generated)
    audience_analysis: Mapped[str] = mapped_column(Text, default="")
    collaboration_opportunity: Mapped[str] = mapped_column(Text, default="")

    # Contact information
    email: Mapped[str] = mapped_column(String(256), default="")
    external_url: Mapped[str] = mapped_column(String(512), default="")
    
    # Existing fields
    external_id: Mapped[str] = mapped_column(String(256), default="")
    platform: Mapped[str] = mapped_column(String(64), default="instagram")
    country: Mapped[str] = mapped_column(String(128), default="")
    gender: Mapped[str] = mapped_column(String(64), default="")
    profile_url: Mapped[str] = mapped_column(String(512), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    results = relationship("RequestResult", back_populates="influencer", cascade="all, delete-orphan")


class RequestResult(Base):
    __tablename__ = "request_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    influencer_id: Mapped[int] = mapped_column(ForeignKey("influencers.id"))

    score: Mapped[float] = mapped_column(Float, default=0)
    rank: Mapped[int] = mapped_column(default=0)

    request = relationship("Request", back_populates="results")
    influencer = relationship("Influencer", back_populates="results")


# ======= Reddit Lead Generation Models =======

class RedditCampaignStatus(str, enum.Enum):
    DISCOVERING = "DISCOVERING"  # Finding subreddits
    ACTIVE = "ACTIVE"  # Polling for leads
    PAUSED = "PAUSED"  # Temporarily stopped
    COMPLETED = "COMPLETED"  # User marked as done
    DELETED = "DELETED"  # Soft deleted by user


class RedditCampaign(Base):
    """
    A Reddit lead generation campaign
    User creates campaign, selects subreddits, we poll them periodically
    """
    __tablename__ = "reddit_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Link to user
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    status: Mapped[RedditCampaignStatus] = mapped_column(
        Enum(RedditCampaignStatus), 
        default=RedditCampaignStatus.DISCOVERING
    )
    
    # User input
    business_description: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(Text, default="")  # Comma-separated keywords
    
    # LLM generated search queries
    search_queries: Mapped[str] = mapped_column(Text, default="")  # JSON list
    
    # Polling configuration
    poll_interval_hours: Mapped[int] = mapped_column(default=6)  # Poll every X hours
    last_poll_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    subreddits = relationship("RedditCampaignSubreddit", back_populates="campaign", cascade="all, delete-orphan")
    leads = relationship("RedditLead", back_populates="campaign", cascade="all, delete-orphan")


class RedditCampaignSubreddit(Base):
    """
    Subreddits selected by user for a campaign
    """
    __tablename__ = "reddit_campaign_subreddits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("reddit_campaigns.id"))
    
    subreddit_name: Mapped[str] = mapped_column(String(128))
    subreddit_title: Mapped[str] = mapped_column(String(512), default="")
    subreddit_description: Mapped[str] = mapped_column(Text, default="")
    subscribers: Mapped[int] = mapped_column(default=0)
    
    # LLM-generated relevance score (0.0 - 1.0)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    
    is_active: Mapped[bool] = mapped_column(default=True)  # User can disable specific subreddits
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    campaign = relationship("RedditCampaign", back_populates="subreddits")


class RedditLeadStatus(str, enum.Enum):
    NEW = "NEW"  # Just discovered (Inbox)
    CONTACTED = "CONTACTED"  # User commented or DMed
    DISMISSED = "DISMISSED"  # User not interested


class RedditLead(Base):
    """
    A Reddit post that might be a lead opportunity
    """
    __tablename__ = "reddit_leads"
    __table_args__ = (
        # 复合唯一约束：同一个 campaign 内帖子不能重复，但不同 campaign 可以有相同帖子
        # 这样每个 campaign 可以独立追踪和评分同一个帖子
        UniqueConstraint('campaign_id', 'reddit_post_id', name='uq_campaign_post'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("reddit_campaigns.id"))

    # Reddit post data - 移除全局唯一约束，改为复合唯一约束（见 __table_args__）
    reddit_post_id: Mapped[str] = mapped_column(String(128), index=True)
    subreddit_name: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(128))
    post_url: Mapped[str] = mapped_column(String(512))
    
    # Engagement metrics
    score: Mapped[int] = mapped_column(default=0)
    num_comments: Mapped[int] = mapped_column(default=0)
    created_utc: Mapped[float] = mapped_column(Float)
    
    # AI analysis - 允许为空（待评分状态）
    relevancy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)  # 0-1, None表示未评分
    relevancy_reason: Mapped[str] = mapped_column(Text, default="")
    suggested_comment: Mapped[str] = mapped_column(Text, default="")
    suggested_dm: Mapped[str] = mapped_column(Text, default="")

    # Lazy suggestion generation tracking
    has_suggestions: Mapped[bool] = mapped_column(Boolean, default=False)
    suggestions_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Lead status
    status: Mapped[RedditLeadStatus] = mapped_column(
        Enum(RedditLeadStatus), 
        default=RedditLeadStatus.NEW
    )
    
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    campaign = relationship("RedditCampaign", back_populates="leads")


# ======= Usage Tracking Models =======

class APIType(str, enum.Enum):
    """API types for usage tracking"""
    REDDIT_APIFY = "REDDIT_APIFY"  # Apify Reddit scraper
    REDDIT_RAPIDAPI = "REDDIT_RAPIDAPI"  # RapidAPI Reddit
    LLM_GEMINI = "LLM_GEMINI"  # Gemini API calls
    LLM_OPENAI = "LLM_OPENAI"  # OpenAI API calls
    EMBEDDING = "EMBEDDING"  # Embedding API calls


class UsageTracking(Base):
    """
    Tracks API usage per user per day.
    Simple counter for ROI calculation and scam detection.
    """
    __tablename__ = "usage_tracking"
    __table_args__ = (
        UniqueConstraint('user_id', 'api_type', 'date', name='uq_user_api_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    api_type: Mapped[APIType] = mapped_column(Enum(APIType), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)  # Date only (no time)

    # Counters
    call_count: Mapped[int] = mapped_column(default=0)

    # Optional: track tokens for LLM calls
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalSubredditPoll(Base):
    """
    Tracks centralized polling of subreddits
    Even if 100 users follow r/SaaS, we only poll it ONCE per cycle
    """
    __tablename__ = "global_subreddit_polls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subreddit_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    last_poll_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_post_timestamp: Mapped[float] = mapped_column(Float, default=0)  # Track last seen post

    poll_count: Mapped[int] = mapped_column(default=0)
    total_posts_found: Mapped[int] = mapped_column(default=0)


class SubredditCache(Base):
    """
    Global subreddit cache table
    Stores all subreddits discovered via search, regardless of user selection.
    Used for:
    1. Avoiding duplicate API calls
    2. Future vector database data source
    """
    __tablename__ = "subreddit_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Basic info from Apify search results
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    subscribers: Mapped[int] = mapped_column(default=0)
    url: Mapped[str] = mapped_column(String(512), default="")
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    reddit_created_utc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Discovery tracking
    discovered_via_queries: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of search queries
    discovery_count: Mapped[int] = mapped_column(default=1)  # Number of times discovered

    # Timestamps
    first_discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Reserved for future vector embedding
    embedding_status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/processing/done
    embedding_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
