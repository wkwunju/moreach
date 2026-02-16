from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import logging
import stripe

from app.core.db import get_db
from app.core.auth import (
    get_password_hash, verify_password, create_access_token, get_current_user,
    create_verification_token, verify_verification_token
)
from app.core.email import send_verification_email, send_welcome_email
from app.models.schemas import (
    RequestCreate, RequestResponse, ResultsResponse, InfluencerResponse,
    # User schemas
    UserRegister, UserLogin, UserResponse, TokenResponse, GoogleAuthRequest, ProfileUpdate,
    # Reddit schemas
    RedditCampaignCreate, RedditCampaignResponse, SubredditInfo,
    RedditSubredditSelect, RedditLeadResponse, RedditLeadUpdateStatus,
    RedditCampaignLeadsResponse
)
from app.models.tables import (
    Request, RequestResult, Influencer,
    # User models
    User,
    # Reddit models
    RedditCampaign, RedditCampaignSubreddit, RedditLead,
    RedditCampaignStatus, RedditLeadStatus,
    # Usage tracking
    APIType, UsageTracking,
    # Poll tracking
    PollJob, PollJobStatus,
)
from app.services.usage_tracking import track_api_call
from app.core.config import settings
from app.services.discovery.manager import DiscoveryManager
from app.services.reddit.discovery import RedditDiscoveryService
from app.services.reddit.cache import SubredditCacheService
from app.services.stripe_billing import (
    create_checkout_session,
    create_customer_portal_session,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_payment_failed,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def user_to_response(user: User) -> UserResponse:
    """Convert a User model to UserResponse schema"""
    from app.core.plan_limits import is_admin_user
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        job_title=user.job_title,
        industry=user.industry.value,
        usage_type=user.usage_type.value,
        role=user.role.value,
        is_active=user.is_active,
        email_verified=user.email_verified,
        profile_completed=user.profile_completed,
        subscription_tier=user.subscription_tier.value,
        trial_ends_at=user.trial_ends_at,
        subscription_ends_at=user.subscription_ends_at,
        is_admin=is_admin_user(user.id),
        created_at=user.created_at,
    )


# ======= Authentication Endpoints =======

@router.post("/auth/register")
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account
    Sends a verification email - user must verify before logging in
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user (email_verified defaults to False)
    # Set trial to end 7 days from now
    trial_end = datetime.utcnow() + timedelta(days=7)

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        company=payload.company,
        job_title=payload.job_title,
        industry=payload.industry,
        usage_type=payload.usage_type,
        profile_completed=True,  # Profile is complete since they filled out the form
        trial_ends_at=trial_end,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send verification email
    verification_token = create_verification_token(user.email)
    email_sent = send_verification_email(user.email, verification_token)

    if not email_sent:
        logger.warning(f"Failed to send verification email to {user.email}")

    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "email": user.email,
        "email_sent": email_sent
    }


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    Requires email to be verified
    """
    # Find user by email
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    # Check if user is blocked (use generic error to not reveal blocked status)
    if user.is_blocked:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )

    # Create access token (sub must be string)
    access_token = create_access_token(data={"sub": str(user.id)})

    # Track last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return user_to_response(current_user)


@router.get("/auth/polling-schedule")
def get_polling_schedule(current_user: User = Depends(get_current_user)):
    """
    Get the user's scheduled polling configuration based on their subscription tier.

    Returns polling frequency and times:
    - Starter plans: 2x/day (UTC 07:00, 16:00)
    - Growth/Pro plans: 4x/day (UTC 07:00, 11:00, 16:00, 22:00)
    """
    from app.services.reddit.scheduler import get_polling_schedule_info

    schedule = get_polling_schedule_info(current_user.subscription_tier)
    return {
        "tier": current_user.subscription_tier.value,
        "schedule": schedule
    }


@router.post("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify email address using the token from the verification email
    """
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link. Please request a new one."
        )

    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.email_verified:
        return {"message": "Email already verified. You can now log in."}

    # Mark email as verified
    user.email_verified = True
    db.commit()

    # Send welcome email
    send_welcome_email(user.email, user.full_name)

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/auth/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    """
    Resend verification email
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If an account exists with this email, a verification email has been sent."}

    if user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    # Send verification email
    verification_token = create_verification_token(user.email)
    email_sent = send_verification_email(user.email, verification_token)

    return {
        "message": "If an account exists with this email, a verification email has been sent.",
        "email_sent": email_sent
    }


@router.post("/auth/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google ID Token (Sign In With Google popup)
    - Verifies the ID token with Google
    - Creates a new user or logs in existing user
    - Returns JWT access token
    """
    import httpx
    from app.core.config import settings

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured"
        )

    # Verify ID token with Google
    try:
        response = httpx.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid Google ID token"
            )

        token_info = response.json()

        # Verify the token was issued for our app
        if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=401,
                detail="Token was not issued for this application"
            )

        google_id = token_info.get("sub")
        email = token_info.get("email")
        name = token_info.get("name", "")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not provided by Google"
            )

    except httpx.RequestError as e:
        logger.error(f"Error verifying Google token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify Google token"
        )

    # Find existing user by google_id or email
    user = db.query(User).filter(
        or_(User.google_id == google_id, User.email == email)
    ).first()

    if user:
        # Check if user is blocked (use generic error)
        if user.is_blocked:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

        # Link Google account if not already linked
        if not user.google_id:
            user.google_id = google_id
            db.commit()
    else:
        # Create new user with 7-day trial
        trial_end = datetime.utcnow() + timedelta(days=7)
        user = User(
            email=email,
            google_id=google_id,
            full_name=name,
            hashed_password=None,  # No password for OAuth users
            email_verified=True,  # Google has already verified the email
            trial_ends_at=trial_end,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send welcome email for new users
        send_welcome_email(user.email, user.full_name)

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Track last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        user=user_to_response(user)
    )


@router.get("/auth/google")
def google_auth_redirect():
    """
    Redirect to Google OAuth authorization page (OAuth 2.0 flow)
    """
    from urllib.parse import urlencode
    from fastapi.responses import RedirectResponse

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured"
        )

    # Build Google OAuth URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/auth/google/callback")
def google_auth_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback - exchange code for tokens and create/login user
    """
    import httpx
    from fastapi.responses import RedirectResponse

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured"
        )

    # Exchange authorization code for tokens
    try:
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{settings.FRONTEND_URL}/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            logger.error(f"Failed to exchange code for token: {token_response.text}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
            )

        tokens = token_response.json()
        id_token = tokens.get("id_token")

        # Verify ID token to get user info
        userinfo_response = httpx.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        )

        if userinfo_response.status_code != 200:
            logger.error(f"Failed to verify ID token: {userinfo_response.text}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
            )

        token_info = userinfo_response.json()

        # Verify the token was issued for our app
        if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=invalid_token"
            )

        google_id = token_info.get("sub")
        email = token_info.get("email")
        name = token_info.get("name", "")

        if not email:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=no_email"
            )

    except httpx.RequestError as e:
        logger.error(f"Error during Google OAuth: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        )

    # Find existing user by google_id or email
    user = db.query(User).filter(
        or_(User.google_id == google_id, User.email == email)
    ).first()

    if user:
        # Check if user is blocked (use generic error)
        if user.is_blocked:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=auth_failed"
            )

        # Link Google account if not already linked
        if not user.google_id:
            user.google_id = google_id
            db.commit()
    else:
        # Create new user with 7-day trial
        trial_end = datetime.utcnow() + timedelta(days=7)
        user = User(
            email=email,
            google_id=google_id,
            full_name=name,
            hashed_password=None,  # No password for OAuth users
            email_verified=True,  # Google has already verified the email
            trial_ends_at=trial_end,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send welcome email for new users
        send_welcome_email(user.email, user.full_name)

    if not user.is_active:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=account_inactive"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Track last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Redirect to frontend with token
    # The frontend will store the token and redirect to dashboard
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/google/callback?token={access_token}&user={user.id}"
    )


@router.post("/auth/complete-profile", response_model=UserResponse)
def complete_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete user profile after OAuth login
    """
    current_user.full_name = payload.full_name
    current_user.company = payload.company
    current_user.job_title = payload.job_title
    current_user.industry = payload.industry
    current_user.usage_type = payload.usage_type
    current_user.profile_completed = True

    db.commit()
    db.refresh(current_user)

    return user_to_response(current_user)


# ======= Influencer Discovery Endpoints =======

@router.post("/requests", response_model=RequestResponse)
def create_request(payload: RequestCreate, db: Session = Depends(get_db)):
    manager = DiscoveryManager()
    request = manager.create_request(db, payload.description, payload.constraints)
    return RequestResponse(id=request.id, status=request.status, created_at=request.created_at)


@router.get("/requests/{request_id}", response_model=RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    request = db.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return RequestResponse(id=request.id, status=request.status, created_at=request.created_at)


@router.get("/requests/{request_id}/results", response_model=ResultsResponse)
def get_results(request_id: int, db: Session = Depends(get_db)):
    request = db.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    results = (
        db.query(RequestResult, Influencer)
        .join(Influencer, Influencer.id == RequestResult.influencer_id)
        .filter(RequestResult.request_id == request.id)
        .order_by(RequestResult.rank.asc())
        .all()
    )

    payload = []
    for result, influencer in results:
        payload.append(
            InfluencerResponse(
                id=influencer.id,
                handle=influencer.handle,
                name=influencer.name,
                bio=influencer.bio,
                profile_summary=influencer.profile_summary,
                category=influencer.category,
                tags=influencer.tags,
                
                # Basic metrics
                followers=influencer.followers,
                avg_likes=influencer.avg_likes,
                avg_comments=influencer.avg_comments,
                avg_video_views=influencer.avg_video_views,
                
                # Peak performance metrics
                highest_likes=influencer.highest_likes,
                highest_comments=influencer.highest_comments,
                highest_video_views=influencer.highest_video_views,
                
                # Post analysis metrics
                post_sharing_percentage=influencer.post_sharing_percentage,
                post_collaboration_percentage=influencer.post_collaboration_percentage,
                
                # Advanced analysis
                audience_analysis=influencer.audience_analysis,
                collaboration_opportunity=influencer.collaboration_opportunity,
                
                # Contact information
                email=influencer.email,
                external_url=influencer.external_url,
                
                # Location and demographics
                country=influencer.country,
                gender=influencer.gender,
                
                profile_url=influencer.profile_url,
                score=result.score,
                rank=result.rank,
            )
        )

    return ResultsResponse(request_id=request.id, status=request.status, results=payload)


# ======= Reddit Lead Generation Endpoints =======


class AnalyzeUrlRequest(BaseModel):
    url: str


class AnalyzeUrlResponse(BaseModel):
    description: str
    url: str


@router.post("/reddit/analyze-url", response_model=AnalyzeUrlResponse)
async def analyze_url(
    payload: AnalyzeUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a website URL and generate a business description.
    Uses Playwright headless browser to render JS-heavy sites,
    then extracts text and uses LLM to generate a description.
    """
    import trafilatura

    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Use Playwright to render the page (handles JS-rendered sites)
    html = None
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=20000)
            html = await page.content()
            await browser.close()
    except Exception as e:
        logger.warning(f"Playwright failed for {url}: {e}, falling back to httpx")

    # Fallback to httpx if Playwright fails
    if not html:
        import httpx
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                })
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")

    # Extract text content
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text or len(text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Could not extract enough content from this URL. Please try a different page.")

    # Truncate to avoid excessive LLM input
    if len(text) > 5000:
        text = text[:5000]

    # Use LLM to generate business description
    from app.services.langchain.config import get_llm
    llm = get_llm()

    prompt = f"""You are helping a business owner create a profile to find potential customers on Reddit.

Analyze the website content below and write a business description from the owner's perspective (use "I" or "We").

Requirements:
- Sentence 1: What the core product/service is (pick the PRIMARY offering, not every feature)
- Sentence 2: Who the target customers are and what pain point it solves
- Sentence 3 (optional): Key differentiator or how it works

Rules:
- Write as the business owner would describe their own business, e.g. "We build an AI-powered tool that..."
- Be specific: mention the product name, category, and concrete use case
- Do NOT list every feature — focus on the main value proposition
- Only include information that is explicitly present in the content
- Keep it under 300 characters if possible

Website URL: {url}
Website content:
---
{text}
---

Write ONLY the business description, nothing else. Write in English."""

    try:
        result = await llm.ainvoke(prompt)
        description = result.content.strip()
    except Exception as e:
        logger.error(f"LLM error analyzing URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze website content")

    return AnalyzeUrlResponse(description=description, url=url)


@router.post("/reddit/campaigns", response_model=RedditCampaignResponse)
def create_reddit_campaign(
    payload: RedditCampaignCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 1: Create a new Reddit lead generation campaign
    - User describes their business
    - LLM generates search queries
    - Returns campaign ID
    """
    discovery_service = RedditDiscoveryService()

    # Generate search queries using LLM
    search_queries = discovery_service.generate_search_queries(payload.business_description)

    # Track LLM usage
    llm_type = APIType.LLM_GEMINI if settings.llm_provider.lower() == "gemini" else APIType.LLM_OPENAI
    track_api_call(db, current_user.id, llm_type)

    # Create campaign linked to current user
    campaign = RedditCampaign(
        user_id=current_user.id,
        business_description=payload.business_description,
        search_queries=json.dumps(search_queries),
        poll_interval_hours=payload.poll_interval_hours,
        status=RedditCampaignStatus.DISCOVERING
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return RedditCampaignResponse(
        id=campaign.id,
        status=campaign.status.value,
        business_description=campaign.business_description,
        search_queries=campaign.search_queries,
        poll_interval_hours=campaign.poll_interval_hours,
        last_poll_at=campaign.last_poll_at,
        created_at=campaign.created_at,
        subreddits_count=0,
        leads_count=0
    )


@router.get("/reddit/campaigns/{campaign_id}/discover-subreddits", response_model=list[SubredditInfo])
def discover_subreddits(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 2: Discover relevant subreddits for the campaign
    - Uses the search queries generated in step 1
    - Returns list of subreddits for user to select from
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    # Parse search queries
    search_queries = json.loads(campaign.search_queries)

    # Discover subreddits
    discovery_service = RedditDiscoveryService()
    subreddits = discovery_service.discover_subreddits(search_queries)

    # Track Reddit API usage
    reddit_api_type = APIType.REDDIT_RAPIDAPI if settings.reddit_api_provider.lower() == "rapidapi" else APIType.REDDIT_APIFY
    track_api_call(db, current_user.id, reddit_api_type)

    # Cache all discovered subreddits (before filtering/ranking)
    cache_service = SubredditCacheService()
    try:
        cached_count = cache_service.cache_subreddits(db, subreddits, search_queries)
        logger.info(f"Cached {cached_count} subreddits to database")
    except Exception as e:
        logger.warning(f"Failed to cache subreddits: {e}")  # Non-blocking error

    # Rank subreddits by relevance to business
    subreddits = discovery_service.rank_subreddits(subreddits, campaign.business_description)

    # Track LLM usage for ranking
    llm_type = APIType.LLM_GEMINI if settings.llm_provider.lower() == "gemini" else APIType.LLM_OPENAI
    track_api_call(db, current_user.id, llm_type)

    # Convert to response format
    return [
        SubredditInfo(
            name=sub["name"],
            title=sub["title"],
            description=sub["description"],
            subscribers=sub["subscribers"],
            url=sub["url"],
            relevance_score=sub.get("relevance_score", 5.0)
        )
        for sub in subreddits
    ]


@router.post("/reddit/campaigns/{campaign_id}/select-subreddits")
def select_subreddits(
    campaign_id: int,
    payload: RedditSubredditSelect,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 3: User selects which subreddits to monitor
    - Saves selected subreddits to campaign
    - Activates campaign for polling
    - Auto-triggers first poll in background
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    # Remove existing subreddits
    db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id
    ).delete()
    db.flush()  # Flush deletion before adding new records
    
    # Add selected subreddits
    # Support both full subreddit info (new) and just names (backward compatibility)
    subreddits_added = 0
    if payload.subreddits:
        # New format: full subreddit info provided
        logger.info(f"Adding {len(payload.subreddits)} subreddits to campaign {campaign_id}")
        for sub_info in payload.subreddits:
            campaign_subreddit = RedditCampaignSubreddit(
                campaign_id=campaign_id,
                subreddit_name=sub_info.get("name", ""),
                subreddit_title=sub_info.get("title", ""),
                subreddit_description=sub_info.get("description", ""),
                subscribers=sub_info.get("subscribers", 0),
                relevance_score=sub_info.get("relevance_score"),  # Save the LLM relevance score
                is_active=True
            )
            db.add(campaign_subreddit)
            subreddits_added += 1
            logger.debug(f"Added subreddit: {sub_info.get('name')}")
    elif payload.subreddit_names:
        # Old format: only names provided, use minimal info
        logger.info(f"Adding {len(payload.subreddit_names)} subreddits (names only) to campaign {campaign_id}")
        for subreddit_name in payload.subreddit_names:
            campaign_subreddit = RedditCampaignSubreddit(
                campaign_id=campaign_id,
                subreddit_name=subreddit_name,
                subreddit_title="",
                subreddit_description="",
                subscribers=0,
                is_active=True
            )
            db.add(campaign_subreddit)
            subreddits_added += 1
            logger.debug(f"Added subreddit: {subreddit_name}")
    
    # Collect subreddit names for rules fetching
    selected_names = []
    if payload.subreddits:
        selected_names = [s.get("name", "") for s in payload.subreddits if s.get("name")]
    elif payload.subreddit_names:
        selected_names = list(payload.subreddit_names)

    # Activate campaign
    campaign.status = RedditCampaignStatus.ACTIVE
    db.commit()
    db.refresh(campaign)  # Refresh to load relationships

    # Verify subreddits were saved
    saved_count = db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id
    ).count()
    logger.info(f"Campaign {campaign_id} activated with {saved_count} subreddits (added: {subreddits_added})")

    # Fetch subreddit rules in background (non-blocking)
    if selected_names:
        import threading

        def fetch_rules_thread():
            from app.core.db import SessionLocal
            from app.services.reddit.cache import SubredditCacheService
            try:
                bg_db = SessionLocal()
                try:
                    cache_service = SubredditCacheService()
                    count = cache_service.fetch_and_cache_rules(bg_db, selected_names)
                    logger.info(f"Fetched rules for {count} subreddits (campaign {campaign_id})")
                finally:
                    bg_db.close()
            except Exception as e:
                logger.error(f"Error fetching subreddit rules: {e}", exc_info=True)

        rules_thread = threading.Thread(target=fetch_rules_thread, daemon=True)
        rules_thread.start()

    # Auto-trigger first poll: use Celery in production, threading locally
    try:
        # Try to use Celery (production)
        from app.workers.tasks import poll_campaign_first
        poll_campaign_first.delay(campaign_id)
        logger.info(f"Scheduled auto-first-poll for campaign {campaign_id} via Celery")
    except Exception as e:
        # Fallback to threading (local development without Celery)
        logger.info(f"Celery not available, using threading for campaign {campaign_id}: {e}")
        import threading

        def run_first_poll_thread():
            """Run first poll in a separate thread to avoid blocking the API"""
            from app.core.db import SessionLocal
            from app.services.reddit.polling import RedditPollingService

            logger.info(f"Starting auto-first-poll for campaign {campaign_id} (in background thread)")
            try:
                bg_db = SessionLocal()
                try:
                    polling_service = RedditPollingService()
                    summary = polling_service.poll_campaign_immediately(bg_db, campaign_id, trigger="first_poll")
                    logger.info(f"Auto-first-poll completed for campaign {campaign_id}: {summary}")
                finally:
                    bg_db.close()
            except Exception as e:
                logger.error(f"Error in auto-first-poll for campaign {campaign_id}: {e}", exc_info=True)

        # Start in a daemon thread so it doesn't block server shutdown
        poll_thread = threading.Thread(target=run_first_poll_thread, daemon=True)
        poll_thread.start()
        logger.info(f"Scheduled auto-first-poll for campaign {campaign_id} in background thread")

    return {"message": f"Campaign activated with {saved_count} subreddits", "first_poll_scheduled": True}


@router.get("/reddit/campaigns/{campaign_id}/subreddits", response_model=list[SubredditInfo])
def get_campaign_subreddits(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all subreddits for a campaign
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    subreddits = db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id
    ).all()
    
    return [
        SubredditInfo(
            name=sub.subreddit_name,
            title=sub.subreddit_title,
            description=sub.subreddit_description,
            subscribers=sub.subscribers,
            url=f"https://reddit.com/r/{sub.subreddit_name}",
            relevance_score=sub.relevance_score if sub.relevance_score is not None else 0.5
        )
        for sub in subreddits
    ]


@router.get("/reddit/campaigns/{campaign_id}/subreddit-rules")
def get_subreddit_rules(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get subreddit rules for all active subreddits in a campaign.
    Returns rules_json and rules_summary from SubredditCache.
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")

    subreddits = db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id,
        RedditCampaignSubreddit.is_active == True
    ).all()

    subreddit_names = [s.subreddit_name for s in subreddits]

    # Look up rules from cache
    from app.models.tables import SubredditCache
    cached = db.query(SubredditCache).filter(
        SubredditCache.name.in_(subreddit_names)
    ).all()

    cache_map = {c.name: c for c in cached}

    # Find subreddits missing rules and trigger background fetch
    missing_rules = [
        name for name in subreddit_names
        if name not in cache_map or not cache_map[name].rules_json
    ]
    if missing_rules:
        import threading

        def fetch_missing_rules():
            from app.core.db import SessionLocal
            from app.services.reddit.cache import SubredditCacheService
            try:
                bg_db = SessionLocal()
                try:
                    cache_service = SubredditCacheService()
                    count = cache_service.fetch_and_cache_rules(bg_db, missing_rules)
                    logger.info(f"Background-fetched rules for {count} subreddits")
                finally:
                    bg_db.close()
            except Exception as e:
                logger.error(f"Error fetching missing subreddit rules: {e}", exc_info=True)

        threading.Thread(target=fetch_missing_rules, daemon=True).start()
        logger.info(f"Triggered background rules fetch for {len(missing_rules)} subreddits: {missing_rules}")

    result = []
    for name in subreddit_names:
        c = cache_map.get(name)
        rules_json = []
        if c and c.rules_json:
            try:
                rules_json = json.loads(c.rules_json)
            except json.JSONDecodeError:
                pass
        result.append({
            "subreddit_name": name,
            "rules": rules_json,
            "rules_summary": c.rules_summary if c else "",
        })

    return result


@router.get("/reddit/campaigns/{campaign_id}", response_model=RedditCampaignResponse)
def get_reddit_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get campaign details
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    subreddits_count = db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id
    ).count()
    
    # Only count scored leads (relevancy_score IS NOT NULL)
    leads_count = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.relevancy_score.isnot(None)
    ).count()

    return RedditCampaignResponse(
        id=campaign.id,
        status=campaign.status.value,
        business_description=campaign.business_description,
        search_queries=campaign.search_queries,
        poll_interval_hours=campaign.poll_interval_hours,
        last_poll_at=campaign.last_poll_at,
        created_at=campaign.created_at,
        subreddits_count=subreddits_count,
        leads_count=leads_count
    )


@router.get("/reddit/campaigns/{campaign_id}/leads", response_model=RedditCampaignLeadsResponse)
def get_campaign_leads(
    campaign_id: int,
    status: Optional[str] = None,
    limit: int = 200,  # Increased default limit
    offset: int = 0,   # Add pagination support
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 4: Get leads for a campaign
    - Returns all discovered leads with relevancy scores and suggested responses
    - Can filter by status (NEW, CONTACTED, DISMISSED)
    - Supports pagination via limit and offset parameters
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    # Build query - filter by campaign
    query = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id
    )
    
    # Only show leads with minimum quality (support both old 0.0-1.0 format and new 0-100 format)
    # If score > 1, use new format (>= 50), otherwise use old format (>= 0.5)
    query = query.filter(
        or_(
            RedditLead.relevancy_score >= 50,  # New format: 50-100
            and_(
                RedditLead.relevancy_score <= 1,  # Old format: 0.0-1.0
                RedditLead.relevancy_score >= 0.5
            )
        )
    )
    
    if status:
        try:
            lead_status = RedditLeadStatus[status]
            query = query.filter(RedditLead.status == lead_status)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Order by relevancy score and recency
    query = query.order_by(
        RedditLead.relevancy_score.desc(),
        RedditLead.discovered_at.desc()
    )
    
    # Get total count (after quality filter)
    total_leads = query.count()

    # Quality filter for counts - same as the main query filter
    quality_filter = or_(
        RedditLead.relevancy_score >= 50,  # New format: 50-100
        and_(
            RedditLead.relevancy_score <= 1,  # Old format: 0.0-1.0
            RedditLead.relevancy_score >= 0.5
        )
    )

    # Get counts by status (only counting leads that pass quality filter)
    new_leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.status == RedditLeadStatus.NEW,
        quality_filter
    ).count()

    contacted_leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.status == RedditLeadStatus.CONTACTED,
        quality_filter
    ).count()
    
    # Apply pagination
    leads = query.offset(offset).limit(limit).all()
    
    # Convert to response format
    lead_responses = [
        RedditLeadResponse(
            id=lead.id,
            reddit_post_id=lead.reddit_post_id,
            subreddit_name=lead.subreddit_name,
            title=lead.title,
            content=lead.content,
            author=lead.author,
            post_url=lead.post_url,
            score=lead.score,
            num_comments=lead.num_comments,
            created_utc=lead.created_utc,
            relevancy_score=lead.relevancy_score,
            relevancy_reason=lead.relevancy_reason,
            suggested_comment=lead.suggested_comment,
            suggested_dm=lead.suggested_dm,
            status=lead.status.value,
            discovered_at=lead.discovered_at
        )
        for lead in leads
    ]
    
    return RedditCampaignLeadsResponse(
        campaign_id=campaign_id,
        total_leads=total_leads,
        new_leads=new_leads,
        contacted_leads=contacted_leads,
        leads=lead_responses
    )


@router.patch("/reddit/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    payload: RedditLeadUpdateStatus,
    db: Session = Depends(get_db)
):
    """
    Step 5: Update lead status (e.g., mark as contacted, dismissed)
    """
    lead = db.get(RedditLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        new_status = RedditLeadStatus[payload.status]
        lead.status = new_status
        db.commit()
        
        return {"message": f"Lead status updated to {payload.status}"}
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")


@router.post("/reddit/campaigns/{campaign_id}/pause")
def pause_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pause a campaign (stop polling)
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    campaign.status = RedditCampaignStatus.PAUSED
    db.commit()
    
    return {"message": "Campaign paused"}


@router.post("/reddit/campaigns/{campaign_id}/resume")
def resume_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resume a paused campaign
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    campaign.status = RedditCampaignStatus.ACTIVE
    db.commit()
    
    return {"message": "Campaign resumed"}



@router.post("/reddit/campaigns/{campaign_id}/run-now")
def run_campaign_now(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger immediate polling for a campaign
    Bypasses the normal 6-hour polling schedule
    """
    from app.services.reddit.polling import RedditPollingService
    
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    if campaign.status != RedditCampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=400, 
            detail=f"Campaign must be ACTIVE to run. Current status: {campaign.status}"
        )
    
    # Log campaign subreddits for debugging
    subreddit_count = len(campaign.subreddits)
    active_count = sum(1 for sub in campaign.subreddits if sub.is_active)
    logger.info(f"Running campaign {campaign_id}: {subreddit_count} total subreddits, {active_count} active")
    if subreddit_count > 0:
        logger.info(f"Subreddits: {[sub.subreddit_name for sub in campaign.subreddits]}")
    
    try:
        polling_service = RedditPollingService()
        summary = polling_service.poll_campaign_immediately(db, campaign_id)
        
        return {
            "message": "Campaign polling completed",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error running campaign {campaign_id} immediately: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run campaign: {str(e)}")


@router.post("/reddit/campaigns/{campaign_id}/poll-async")
def start_poll_async(
    campaign_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a background poll task for a campaign.

    Returns immediately with a task_id. Use the poll-status endpoint
    to check progress. The task continues running even if the page is closed.

    Args:
        force: If True, clears any existing stuck task status and starts fresh
    """
    from app.workers.tasks import poll_campaign_background, get_poll_task_status, clear_poll_task_status

    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")

    if campaign.status != RedditCampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be ACTIVE to run. Current status: {campaign.status}"
        )

    # Check if a poll is already running for this campaign
    existing_status = get_poll_task_status(campaign_id)
    if existing_status and existing_status.get("status") == "running":
        if force:
            # Clear the stuck status
            logger.info(f"Force clearing stuck poll status for campaign {campaign_id}")
            clear_poll_task_status(campaign_id)
        else:
            return {
                "message": "Poll already in progress",
                "task_id": existing_status.get("task_id"),
                "already_running": True
            }

    # Start the background task
    try:
        task = poll_campaign_background.delay(campaign_id)
        logger.info(f"Started background poll for campaign {campaign_id}, task_id={task.id}")

        return {
            "message": "Poll started",
            "task_id": task.id,
            "already_running": False
        }
    except Exception as e:
        logger.error(f"Failed to start background poll for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start poll: {str(e)}")


@router.get("/reddit/campaigns/{campaign_id}/poll-status")
def get_poll_status(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a running or completed poll task.

    Returns progress information including:
    - status: "running" | "completed" | "failed" | null (no task)
    - phase: Current phase of polling
    - current/total: Progress numbers
    - message: Human-readable status message
    - leads_created: Number of leads created so far
    - leads: List of lead IDs created
    - error: Error message if failed
    """
    from app.workers.tasks import get_poll_task_status

    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")

    status = get_poll_task_status(campaign_id)

    if not status:
        return {
            "status": None,
            "message": "No active or recent poll task"
        }

    return status


@router.get("/reddit/campaigns/{campaign_id}/run-now/stream")
async def run_campaign_stream(
    campaign_id: int,
    request: StarletteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SSE streaming endpoint for real-time polling progress

    Event types:
    - progress: {"phase": "fetching"|"scoring"|"suggestions", "current": N, "total": M}
    - lead: {"id": N, "title": "...", "relevancy_score": 90, ...}
    - complete: {"total_leads": N, "total_posts_fetched": M, "summary": {...}}
    - error: {"message": "..."}
    """
    from fastapi.responses import StreamingResponse
    from app.services.reddit.streaming_poll import StreamingPollService
    import json

    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")

    if campaign.status != RedditCampaignStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be ACTIVE to run. Current status: {campaign.status}"
        )

    async def event_generator():
        try:
            service = StreamingPollService()

            async for event in service.poll_campaign_streaming(db, campaign_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from SSE stream for campaign {campaign_id}")
                    break

                yield f"event: {event['type']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream for campaign {campaign_id}: {e}", exc_info=True)
            yield f"event: error\n"
            yield f"data: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/reddit/leads/{lead_id}/generate-suggestions")
async def generate_lead_suggestions(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    On-demand generation of suggested_comment and suggested_dm
    Called when user clicks into a lead that doesn't have suggestions yet
    """
    from datetime import datetime
    from app.services.reddit.batch_scoring import BatchScoringService

    lead = db.get(RedditLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Verify ownership via campaign
    campaign = db.get(RedditCampaign, lead.campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this lead")

    # Check if suggestions already exist
    if lead.has_suggestions and lead.suggested_comment and lead.suggested_dm:
        return {
            "suggested_comment": lead.suggested_comment,
            "suggested_dm": lead.suggested_dm,
            "cached": True
        }

    # Generate suggestions
    scoring_service = BatchScoringService()
    post_dict = {
        "title": lead.title,
        "content": lead.content,
        "subreddit_name": lead.subreddit_name,
        "author": lead.author or "",
        "relevancy_reason": lead.relevancy_reason or "Relevant post"
    }

    try:
        suggestions = await scoring_service.generate_suggestion_on_demand(
            post_dict,
            campaign.business_description
        )

        # Update lead
        lead.suggested_comment = suggestions.get("suggested_comment", "")
        lead.suggested_dm = suggestions.get("suggested_dm", "")
        lead.has_suggestions = True
        lead.suggestions_generated_at = datetime.utcnow()
        db.commit()

        return {
            "suggested_comment": lead.suggested_comment,
            "suggested_dm": lead.suggested_dm,
            "cached": False
        }

    except Exception as e:
        logger.error(f"Error generating suggestions for lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.delete("/reddit/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a campaign (marks status as DELETED but remains in database)
    """
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    campaign.status = RedditCampaignStatus.DELETED
    db.commit()
    
    return {"message": "Campaign deleted successfully"}


@router.get("/reddit/campaigns", response_model=list[RedditCampaignResponse])
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all non-deleted campaigns for the current user
    """
    campaigns = db.query(RedditCampaign).filter(
        RedditCampaign.user_id == current_user.id,
        RedditCampaign.status != RedditCampaignStatus.DELETED
    ).order_by(RedditCampaign.created_at.desc()).all()
    
    responses = []
    for campaign in campaigns:
        subreddits_count = db.query(RedditCampaignSubreddit).filter(
            RedditCampaignSubreddit.campaign_id == campaign.id
        ).count()
        
        # Only count scored leads (relevancy_score IS NOT NULL)
        leads_count = db.query(RedditLead).filter(
            RedditLead.campaign_id == campaign.id,
            RedditLead.relevancy_score.isnot(None)
        ).count()

        responses.append(RedditCampaignResponse(
            id=campaign.id,
            status=campaign.status.value,
            business_description=campaign.business_description,
            search_queries=campaign.search_queries,
            poll_interval_hours=campaign.poll_interval_hours,
            last_poll_at=campaign.last_poll_at,
            created_at=campaign.created_at,
            subreddits_count=subreddits_count,
            leads_count=leads_count
        ))

    return responses


# ============================================================================
# Stripe Billing Endpoints
# ============================================================================

class CheckoutRequest(BaseModel):
    tier_code: str  # e.g., "STARTER_MONTHLY", "GROWTH_ANNUALLY"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.post("/billing/create-checkout-session")
def create_stripe_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for subscription.

    Returns a URL to redirect the user to Stripe's checkout page.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")

    # Default URLs
    frontend_url = settings.FRONTEND_URL
    success_url = request.success_url or f"{frontend_url}/reddit?checkout=success"
    cancel_url = request.cancel_url or f"{frontend_url}/reddit?checkout=cancelled"

    try:
        result = create_checkout_session(
            user=current_user,
            tier_code=request.tier_code,
            db=db,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/billing/create-portal-session")
def create_stripe_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe Customer Portal session for managing subscriptions.

    Returns a URL to redirect the user to Stripe's customer portal.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")

    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    frontend_url = settings.FRONTEND_URL
    return_url = f"{frontend_url}/reddit"

    try:
        result = create_customer_portal_session(
            user=current_user,
            db=db,
            return_url=return_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/billing/webhook")
async def stripe_webhook(
    request: StarletteRequest,
    db: Session = Depends(get_db),
):
    """
    Handle Stripe webhook events.

    This endpoint receives events from Stripe when subscription status changes.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event["type"]
    event_object = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            handle_checkout_completed(event_object, db)

        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(event_object, db)

        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(event_object, db)

        elif event_type == "invoice.payment_failed":
            handle_invoice_payment_failed(event_object, db)

        else:
            logger.info(f"Unhandled event type: {event_type}")

    except Exception as e:
        logger.error(f"Error handling webhook {event_type}: {e}")
        # Don't raise - return 200 so Stripe doesn't retry
        return {"status": "error", "message": str(e)}

    return {"status": "success"}


# ====== Usage Tracking Endpoints ======

from app.services.usage_tracking import get_user_usage_summary, get_all_users_usage
from app.models.tables import UserRole


@router.get("/usage/me")
def get_my_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's API usage stats.
    Optional date filters: start_date and end_date in YYYY-MM-DD format.
    """
    from datetime import date

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    summary = get_user_usage_summary(db, current_user.id, parsed_start, parsed_end)

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "start_date": start_date,
        "end_date": end_date,
        "usage": summary
    }


@router.get("/admin/usage")
def get_all_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint: Get all users' API usage stats.
    Requires admin role.
    """
    # Check admin role
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import date

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            parsed_end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    usage_data = get_all_users_usage(db, parsed_start, parsed_end)

    # Enrich with user emails
    for item in usage_data:
        user = db.get(User, item["user_id"])
        if user:
            item["email"] = user.email

    return {
        "start_date": start_date,
        "end_date": end_date,
        "users": usage_data
    }


# ====== Plan Limits Endpoints ======

from app.services.plan_usage import (
    get_usage_status,
    get_subreddit_limit_status,
    check_can_create_profile,
    check_can_add_subreddits,
    check_subreddit_selection,
)
from app.core.plan_limits import get_plan_limits, get_tier_group


@router.get("/plan/usage")
def get_plan_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's plan usage status.
    Returns profile count, limits, and whether user can create more profiles.
    """
    status = get_usage_status(db, current_user)

    return {
        "profile_count": status.profile_count,
        "max_profiles": status.max_profiles,
        "profiles_remaining": status.profiles_remaining,
        "can_create_profile": status.can_create_profile,
        "current_plan": status.current_plan,
        "tier_group": status.tier_group,
        "next_tier": status.next_tier,
    }


@router.get("/plan/limits")
def get_plan_limits_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the limits for the user's current plan.
    """
    limits = get_plan_limits(current_user.subscription_tier, user_id=current_user.id)
    tier_group = get_tier_group(current_user.subscription_tier)

    return {
        "plan_name": limits.plan_name,
        "tier_group": tier_group,
        "max_profiles": limits.max_profiles,
        "max_subreddits_per_profile": limits.max_subreddits_per_profile,
        "max_leads_per_month": limits.max_leads_per_month,
        "polls_per_day": limits.polls_per_day,
        "next_tier": limits.next_tier,
    }


@router.get("/plan/check-create-profile")
def check_create_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if user can create a new business profile.
    Returns allowed status and upgrade info if limit reached.
    """
    result = check_can_create_profile(db, current_user)

    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "current_count": result.current_count,
        "max_count": result.max_count,
        "upgrade_to": result.upgrade_to,
        "current_plan": result.current_plan,
    }


@router.get("/plan/check-subreddit-limit/{campaign_id}")
def check_subreddit_limit(
    campaign_id: int,
    count: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if user can select the specified number of subreddits for a campaign.

    Args:
        campaign_id: The campaign ID
        count: Number of subreddits user wants to select
    """
    # Verify campaign belongs to user
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    result = check_subreddit_selection(db, current_user, campaign_id, count)

    return {
        "allowed": result.allowed,
        "reason": result.reason,
        "selected_count": result.current_count,
        "max_count": result.max_count,
        "upgrade_to": result.upgrade_to,
        "current_plan": result.current_plan,
    }


@router.get("/plan/campaign/{campaign_id}/subreddit-status")
def get_campaign_subreddit_status(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the subreddit limit status for a specific campaign.
    """
    # Verify campaign belongs to user
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    status = get_subreddit_limit_status(db, current_user, campaign_id)

    return {
        "current_count": status.current_count,
        "max_count": status.max_count,
        "can_add_more": status.can_add_more,
        "remaining": status.remaining,
        "current_plan": status.current_plan,
        "tier_group": status.tier_group,
        "next_tier": status.next_tier,
    }


# ======= Admin Dashboard =======

ADMIN_DASHBOARD_EMAIL = "wkwunju@gmail.com"


def require_admin_dashboard(
    current_user: User = Depends(get_current_user),
) -> User:
    """Only allow the admin email; return 404 to hide endpoint existence."""
    if current_user.email != ADMIN_DASHBOARD_EMAIL:
        raise HTTPException(status_code=404, detail="Not found")
    return current_user


@router.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_dashboard),
):
    now = datetime.utcnow()
    day7 = now - timedelta(days=7)
    day30 = now - timedelta(days=30)

    # --- 1. Overview ---
    total_users = db.query(func.count(User.id)).scalar()
    active_7d = db.query(func.count(User.id)).filter(User.last_login_at >= day7).scalar()
    new_7d = db.query(func.count(User.id)).filter(User.created_at >= day7).scalar()
    new_30d = db.query(func.count(User.id)).filter(User.created_at >= day30).scalar()

    total_campaigns = db.query(func.count(RedditCampaign.id)).scalar()
    active_campaigns = db.query(func.count(RedditCampaign.id)).filter(
        RedditCampaign.status == RedditCampaignStatus.ACTIVE
    ).scalar()

    total_leads = db.query(func.count(RedditLead.id)).scalar()
    contacted_leads = db.query(func.count(RedditLead.id)).filter(
        RedditLead.status == RedditLeadStatus.CONTACTED
    ).scalar()
    contact_rate = round(contacted_leads / total_leads * 100, 1) if total_leads else 0

    # --- 2. User Growth (last 30 days) ---
    growth_rows = (
        db.query(
            func.date(User.created_at).label("day"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= day30)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    user_growth = [{"date": str(r.day), "count": r.count} for r in growth_rows]

    # --- 3. Retention buckets ---
    active_24h = db.query(func.count(User.id)).filter(
        User.last_login_at >= now - timedelta(hours=24)
    ).scalar()
    active_1_7d = db.query(func.count(User.id)).filter(
        User.last_login_at >= day7,
        User.last_login_at < now - timedelta(hours=24),
    ).scalar()
    active_7_30d = db.query(func.count(User.id)).filter(
        User.last_login_at >= day30,
        User.last_login_at < day7,
    ).scalar()
    active_30d_plus = db.query(func.count(User.id)).filter(
        User.last_login_at < day30,
    ).scalar()
    never_logged = db.query(func.count(User.id)).filter(
        User.last_login_at.is_(None),
    ).scalar()

    retention = {
        "active_24h": active_24h,
        "active_1_7d": active_1_7d,
        "active_7_30d": active_7_30d,
        "active_30d_plus": active_30d_plus,
        "never_logged_in": never_logged,
    }

    # --- 4. API Usage (last 30 days) ---
    usage_rows = (
        db.query(
            func.date(UsageTracking.date).label("day"),
            UsageTracking.api_type,
            func.sum(UsageTracking.call_count).label("calls"),
            func.sum(UsageTracking.input_tokens).label("input_tokens"),
            func.sum(UsageTracking.output_tokens).label("output_tokens"),
        )
        .filter(UsageTracking.date >= day30)
        .group_by(func.date(UsageTracking.date), UsageTracking.api_type)
        .order_by(func.date(UsageTracking.date))
        .all()
    )
    api_usage = [
        {
            "date": str(r.day),
            "api_type": r.api_type.value if hasattr(r.api_type, "value") else str(r.api_type),
            "calls": r.calls,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
        }
        for r in usage_rows
    ]

    # --- 5. LLM Costs ---
    COST_PER_MILLION = {
        "LLM_GEMINI": {"input": 0.075, "output": 0.30},
        "LLM_OPENAI": {"input": 0.15, "output": 0.60},
        "EMBEDDING": {"input": 0.02, "output": 0.00},
    }
    llm_rows = (
        db.query(
            UsageTracking.api_type,
            func.sum(UsageTracking.call_count).label("calls"),
            func.sum(UsageTracking.input_tokens).label("input_tokens"),
            func.sum(UsageTracking.output_tokens).label("output_tokens"),
        )
        .filter(UsageTracking.api_type.in_([APIType.LLM_GEMINI, APIType.LLM_OPENAI, APIType.EMBEDDING]))
        .group_by(UsageTracking.api_type)
        .all()
    )
    llm_costs = []
    for r in llm_rows:
        key = r.api_type.value if hasattr(r.api_type, "value") else str(r.api_type)
        rates = COST_PER_MILLION.get(key, {"input": 0, "output": 0})
        cost = (r.input_tokens / 1_000_000 * rates["input"]) + (r.output_tokens / 1_000_000 * rates["output"])
        llm_costs.append({
            "api_type": key,
            "calls": r.calls,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "estimated_cost_usd": round(cost, 4),
        })

    # --- 6. Per-User Table ---
    users = db.query(User).order_by(User.created_at.desc()).all()
    per_user = []
    for u in users:
        campaign_count = db.query(func.count(RedditCampaign.id)).filter(
            RedditCampaign.user_id == u.id,
            RedditCampaign.status != RedditCampaignStatus.DELETED,
        ).scalar()
        lead_count = (
            db.query(func.count(RedditLead.id))
            .join(RedditCampaign, RedditLead.campaign_id == RedditCampaign.id)
            .filter(RedditCampaign.user_id == u.id)
            .scalar()
        )
        contacted_count = (
            db.query(func.count(RedditLead.id))
            .join(RedditCampaign, RedditLead.campaign_id == RedditCampaign.id)
            .filter(RedditCampaign.user_id == u.id, RedditLead.status == RedditLeadStatus.CONTACTED)
            .scalar()
        )
        api_calls = db.query(func.sum(UsageTracking.call_count)).filter(
            UsageTracking.user_id == u.id
        ).scalar() or 0

        per_user.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "subscription_tier": u.subscription_tier.value,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "campaigns": campaign_count,
            "leads": lead_count,
            "contacted": contacted_count,
            "contact_rate": round(contacted_count / lead_count * 100, 1) if lead_count else 0,
            "api_calls": api_calls,
        })

    # --- 7. Campaign Health (last 7 days) ---
    poll_total = db.query(func.count(PollJob.id)).filter(PollJob.started_at >= day7).scalar()
    poll_ok = db.query(func.count(PollJob.id)).filter(
        PollJob.started_at >= day7, PollJob.status == PollJobStatus.COMPLETED
    ).scalar()
    poll_fail = db.query(func.count(PollJob.id)).filter(
        PollJob.started_at >= day7, PollJob.status == PollJobStatus.FAILED
    ).scalar()
    avg_leads = db.query(func.avg(PollJob.leads_created)).filter(
        PollJob.started_at >= day7, PollJob.status == PollJobStatus.COMPLETED
    ).scalar()

    campaign_health = {
        "total_polls_7d": poll_total,
        "successful": poll_ok,
        "failed": poll_fail,
        "success_rate": round(poll_ok / poll_total * 100, 1) if poll_total else 0,
        "avg_leads_per_poll": round(float(avg_leads), 1) if avg_leads else 0,
    }

    return {
        "generated_at": now.isoformat(),
        "overview": {
            "total_users": total_users,
            "active_users_7d": active_7d,
            "new_users_7d": new_7d,
            "new_users_30d": new_30d,
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_leads": total_leads,
            "contacted_leads": contacted_leads,
            "contact_rate": contact_rate,
        },
        "user_growth": user_growth,
        "retention": retention,
        "api_usage": api_usage,
        "llm_costs": llm_costs,
        "per_user": per_user,
        "campaign_health": campaign_health,
    }
