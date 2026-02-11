from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, model_validator, Field

from app.models.tables import RequestStatus, IndustryType, UsageType


# ======= User Authentication Schemas =======

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, description="Full name is required")
    company: str = ""
    job_title: str = ""
    industry: IndustryType
    usage_type: UsageType


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google ID token from Sign In With Google")


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company: str
    job_title: str
    industry: str
    usage_type: str
    role: str
    is_active: bool
    email_verified: bool
    profile_completed: bool
    subscription_tier: str
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    is_admin: bool = False
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Schema for completing user profile after OAuth login"""
    full_name: str = Field(..., min_length=1, description="Full name is required")
    company: str = ""
    job_title: str = ""
    industry: IndustryType
    usage_type: UsageType


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RequestCreate(BaseModel):
    description: str
    constraints: str = ""


class RequestResponse(BaseModel):
    id: int
    status: RequestStatus
    created_at: datetime


class InfluencerResponse(BaseModel):
    id: int
    handle: str
    name: str
    bio: str
    profile_summary: str
    category: str
    tags: str
    
    # Basic metrics
    followers: float
    avg_likes: float
    avg_comments: float
    avg_video_views: float
    
    # Peak performance metrics
    highest_likes: float
    highest_comments: float
    highest_video_views: float
    
    # Post analysis metrics
    post_sharing_percentage: float
    post_collaboration_percentage: float
    
    # Advanced analysis
    audience_analysis: str
    collaboration_opportunity: str
    
    # Contact information
    email: str
    external_url: str
    
    # Location and demographics
    country: str
    gender: str
    
    profile_url: str
    score: float
    rank: int


class ResultsResponse(BaseModel):
    request_id: int
    status: RequestStatus
    results: List[InfluencerResponse]


# ======= Reddit Lead Generation Schemas =======

class RedditCampaignCreate(BaseModel):
    business_description: str
    poll_interval_hours: int = 6


class SubredditInfo(BaseModel):
    name: str
    title: str
    description: str
    subscribers: int
    url: str
    relevance_score: float = 5.0


class RedditCampaignResponse(BaseModel):
    id: int
    status: str
    business_description: str
    search_queries: str
    poll_interval_hours: int
    last_poll_at: Optional[datetime]
    created_at: datetime
    subreddits_count: int = 0
    leads_count: int = 0


class RedditSubredditSelect(BaseModel):
    subreddit_names: Optional[List[str]] = None  # Deprecated: use subreddits instead
    subreddits: Optional[List[Dict[str, Any]]] = None  # Full subreddit info
    
    @model_validator(mode='after')
    def check_at_least_one(self):
        if not self.subreddit_names and not self.subreddits:
            raise ValueError('Either subreddit_names or subreddits must be provided')
        return self


class RedditLeadResponse(BaseModel):
    id: int
    reddit_post_id: str
    subreddit_name: str
    title: str
    content: str
    author: str
    post_url: str
    score: int
    num_comments: int
    created_utc: float
    relevancy_score: Optional[float]  # 允许为空（待评分状态）
    relevancy_reason: str
    suggested_comment: str
    suggested_dm: str
    status: str
    discovered_at: datetime


class RedditLeadUpdateStatus(BaseModel):
    status: str  # "NEW", "CONTACTED", "DISMISSED"


class RedditCampaignLeadsResponse(BaseModel):
    campaign_id: int
    total_leads: int
    new_leads: int
    contacted_leads: int
    leads: List[RedditLeadResponse]
