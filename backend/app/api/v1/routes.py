from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
import json
import logging

from app.core.db import get_db
from app.core.auth import (
    get_password_hash, verify_password, create_access_token, get_current_user
)
from app.models.schemas import (
    RequestCreate, RequestResponse, ResultsResponse, InfluencerResponse,
    # User schemas
    UserRegister, UserLogin, UserResponse, TokenResponse,
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
    RedditCampaignStatus, RedditLeadStatus
)
from app.services.discovery.manager import DiscoveryManager
from app.services.reddit.discovery import RedditDiscoveryService
from app.services.reddit.cache import SubredditCacheService

router = APIRouter()
logger = logging.getLogger(__name__)


# ======= Authentication Endpoints =======

@router.post("/auth/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        company=payload.company,
        job_title=payload.job_title,
        industry=payload.industry,
        usage_type=payload.usage_type,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token (sub must be string)
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
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
            created_at=user.created_at,
        )
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    """
    # Find user by email
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )
    
    # Create access token (sub must be string)
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
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
            created_at=user.created_at,
        )
    )


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company=current_user.company,
        job_title=current_user.job_title,
        industry=current_user.industry.value,
        usage_type=current_user.usage_type.value,
        role=current_user.role.value,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
    )


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

    # Cache all discovered subreddits (before filtering/ranking)
    cache_service = SubredditCacheService()
    try:
        cached_count = cache_service.cache_subreddits(db, subreddits, search_queries)
        logger.info(f"Cached {cached_count} subreddits to database")
    except Exception as e:
        logger.warning(f"Failed to cache subreddits: {e}")  # Non-blocking error

    # Rank subreddits by relevance to business
    subreddits = discovery_service.rank_subreddits(subreddits, campaign.business_description)

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 3: User selects which subreddits to monitor
    - Saves selected subreddits to campaign
    - Activates campaign for polling
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
    
    # Activate campaign
    campaign.status = RedditCampaignStatus.ACTIVE
    db.commit()
    db.refresh(campaign)  # Refresh to load relationships
    
    # Verify subreddits were saved
    saved_count = db.query(RedditCampaignSubreddit).filter(
        RedditCampaignSubreddit.campaign_id == campaign_id
    ).count()
    logger.info(f"Campaign {campaign_id} activated with {saved_count} subreddits (added: {subreddits_added})")
    
    return {"message": f"Campaign activated with {saved_count} subreddits"}


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
    
    leads_count = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id
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
    status: str | None = None,
    limit: int = 200,  # Increased default limit
    offset: int = 0,   # Add pagination support
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 4: Get leads for a campaign
    - Returns all discovered leads with relevancy scores and suggested responses
    - Can filter by status (NEW, REVIEWED, CONTACTED, DISMISSED)
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
    
    # Get total count
    total_leads = query.count()
    
    # Get counts by status
    new_leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.status == RedditLeadStatus.NEW
    ).count()
    
    reviewed_leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.status == RedditLeadStatus.REVIEWED
    ).count()
    
    contacted_leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.status == RedditLeadStatus.CONTACTED
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
        reviewed_leads=reviewed_leads,
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


@router.post("/reddit/campaigns/{campaign_id}/rescore-leads")
def rescore_campaign_leads(
    campaign_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rescore all leads for a campaign that have no relevancy score
    Useful for fixing leads that failed to score initially
    """
    from app.services.reddit.polling import RedditPollingService
    from app.services.reddit.scoring import RedditScoringService
    
    campaign = db.get(RedditCampaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign belongs to current user
    if campaign.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    
    # Get all leads without scores
    leads = db.query(RedditLead).filter(
        RedditLead.campaign_id == campaign_id,
        RedditLead.relevancy_score.is_(None)
    ).all()
    
    if not leads:
        return {"message": "No leads need rescoring", "rescored": 0, "deleted": 0}
    
    logger.info(f"Rescoring {len(leads)} leads for campaign {campaign_id}")
    
    scoring_service = RedditScoringService()
    scored_count = 0
    deleted_count = 0
    
    for lead in leads:
        try:
            post_dict = {
                "id": lead.reddit_post_id,
                "title": lead.title,
                "content": lead.content,
                "author": lead.author,
                "url": lead.post_url,
                "score": lead.score,
                "num_comments": lead.num_comments,
                "created_utc": lead.created_utc,
                "subreddit_name": lead.subreddit_name
            }
            
            score_result = scoring_service.score_post(
                post=post_dict,
                business_description=campaign.business_description
            )
            
            lead.relevancy_score = score_result["relevancy_score"]
            lead.relevancy_reason = score_result["relevancy_reason"]
            lead.suggested_comment = score_result["suggested_comment"]
            lead.suggested_dm = score_result["suggested_dm"]
            
            scored_count += 1
            
            # Delete low-relevancy leads (< 50%)
            if lead.relevancy_score < 50:
                db.delete(lead)
                deleted_count += 1
            
            # 立即写入数据库！不要等所有都处理完
            db.commit()
            logger.info(f"Scored and saved lead {lead.id}: {lead.relevancy_score}")
                
        except Exception as e:
            logger.error(f"Error scoring lead {lead.id}: {e}", exc_info=True)
            db.rollback()  # 回滚失败的事务
            continue
    
    return {
        "message": f"Rescored {scored_count} leads, deleted {deleted_count} low-relevancy leads",
        "rescored": scored_count,
        "deleted": deleted_count,
        "kept": scored_count - deleted_count
    }


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
        
        leads_count = db.query(RedditLead).filter(
            RedditLead.campaign_id == campaign.id
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
