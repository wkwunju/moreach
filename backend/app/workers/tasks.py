import logging
import json
import redis
from datetime import datetime
from sqlalchemy import select
from typing import Optional

from app.core.db import SessionLocal
from app.core.config import settings
from app.models.tables import Request, Influencer, RequestResult, RequestStatus
from app.services.discovery.pipeline import DiscoveryPipeline
from app.services.discovery.search import DiscoverySearch
from app.services.reddit.polling import RedditPollingService
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)

# Redis client for task progress tracking
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client for progress tracking"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def get_poll_task_key(campaign_id: int) -> str:
    """Get Redis key for poll task status"""
    return f"poll_task:campaign:{campaign_id}"


def set_poll_task_status(campaign_id: int, status: dict) -> None:
    """Store poll task status in Redis"""
    r = get_redis_client()
    key = get_poll_task_key(campaign_id)
    r.setex(key, 3600, json.dumps(status))  # Expire after 1 hour


def get_poll_task_status(campaign_id: int) -> Optional[dict]:
    """Get poll task status from Redis"""
    r = get_redis_client()
    key = get_poll_task_key(campaign_id)
    data = r.get(key)
    if data:
        return json.loads(data)
    return None


def clear_poll_task_status(campaign_id: int) -> None:
    """Clear poll task status from Redis"""
    r = get_redis_client()
    key = get_poll_task_key(campaign_id)
    r.delete(key)


@celery_app.task(name="app.workers.tasks.run_discovery")
def run_discovery(request_id: int) -> None:
    db = SessionLocal()
    try:
        request = db.get(Request, request_id)
        if not request:
            return
        logger.info("Discovery job started: request_id=%s", request_id)
        request.status = RequestStatus.PROCESSING
        db.commit()

        pipeline = DiscoveryPipeline()
        candidates = pipeline.run(request.description, request.constraints)

        for candidate in candidates:
            influencer = db.execute(
                select(Influencer).where(Influencer.handle == candidate.handle)
            ).scalar_one_or_none()
            if not influencer:
                # Create new influencer
                influencer = Influencer(
                    handle=candidate.handle,
                    name=candidate.name,
                    bio=candidate.bio,
                    profile_summary=candidate.profile_summary,
                    category=candidate.category,
                    tags=candidate.tags,
                    followers=candidate.followers,
                    avg_likes=candidate.avg_likes,
                    avg_comments=candidate.avg_comments,
                    avg_video_views=candidate.avg_video_views,
                    highest_likes=candidate.highest_likes,
                    highest_comments=candidate.highest_comments,
                    highest_video_views=candidate.highest_video_views,
                    post_sharing_percentage=candidate.post_sharing_percentage,
                    post_collaboration_percentage=candidate.post_collaboration_percentage,
                    audience_analysis=candidate.audience_analysis,
                    collaboration_opportunity=candidate.collaboration_opportunity,
                    email=candidate.email,
                    external_url=candidate.external_url,
                    profile_url=candidate.profile_url,
                    platform="instagram",
                    country=candidate.country,
                    gender=candidate.gender,
                )
                db.add(influencer)
                logger.info(f"Created new influencer: @{candidate.handle}")
            else:
                # ✅✅✅ Update existing influencer with new data ✅✅✅
                updated_fields = []
                
                # Update all fields with new candidate data
                if candidate.name and candidate.name != influencer.name:
                    influencer.name = candidate.name
                    updated_fields.append("name")
                
                if candidate.bio and candidate.bio != influencer.bio:
                    influencer.bio = candidate.bio
                    updated_fields.append("bio")
                
                if candidate.profile_summary and candidate.profile_summary != influencer.profile_summary:
                    influencer.profile_summary = candidate.profile_summary
                    updated_fields.append("profile_summary")
                
                if candidate.category and candidate.category != influencer.category:
                    influencer.category = candidate.category
                    updated_fields.append("category")
                
                if candidate.tags and candidate.tags != influencer.tags:
                    influencer.tags = candidate.tags
                    updated_fields.append("tags")
                
                if candidate.audience_analysis and candidate.audience_analysis != influencer.audience_analysis:
                    influencer.audience_analysis = candidate.audience_analysis
                    updated_fields.append("audience_analysis")
                
                if candidate.collaboration_opportunity and candidate.collaboration_opportunity != influencer.collaboration_opportunity:
                    influencer.collaboration_opportunity = candidate.collaboration_opportunity
                    updated_fields.append("collaboration_opportunity")
                
                if candidate.email and candidate.email != influencer.email:
                    influencer.email = candidate.email
                    updated_fields.append("email")
                
                if candidate.external_url and candidate.external_url != influencer.external_url:
                    influencer.external_url = candidate.external_url
                    updated_fields.append("external_url")
                
                if candidate.country and candidate.country != influencer.country:
                    influencer.country = candidate.country
                    updated_fields.append("country")
                
                if candidate.gender and candidate.gender != influencer.gender:
                    influencer.gender = candidate.gender
                    updated_fields.append("gender")
                
                # Update numeric fields
                if candidate.followers != influencer.followers:
                    influencer.followers = candidate.followers
                    updated_fields.append("followers")
                
                if candidate.avg_likes != influencer.avg_likes:
                    influencer.avg_likes = candidate.avg_likes
                    updated_fields.append("avg_likes")
                
                if candidate.avg_comments != influencer.avg_comments:
                    influencer.avg_comments = candidate.avg_comments
                    updated_fields.append("avg_comments")
                
                if candidate.avg_video_views != influencer.avg_video_views:
                    influencer.avg_video_views = candidate.avg_video_views
                    updated_fields.append("avg_video_views")
                
                if candidate.highest_likes != influencer.highest_likes:
                    influencer.highest_likes = candidate.highest_likes
                    updated_fields.append("highest_likes")
                
                if candidate.highest_comments != influencer.highest_comments:
                    influencer.highest_comments = candidate.highest_comments
                    updated_fields.append("highest_comments")
                
                if candidate.highest_video_views != influencer.highest_video_views:
                    influencer.highest_video_views = candidate.highest_video_views
                    updated_fields.append("highest_video_views")
                
                if candidate.post_sharing_percentage != influencer.post_sharing_percentage:
                    influencer.post_sharing_percentage = candidate.post_sharing_percentage
                    updated_fields.append("post_sharing_percentage")
                
                if candidate.post_collaboration_percentage != influencer.post_collaboration_percentage:
                    influencer.post_collaboration_percentage = candidate.post_collaboration_percentage
                    updated_fields.append("post_collaboration_percentage")
                
                if updated_fields:
                    logger.info(f"Updated existing influencer @{candidate.handle}: {', '.join(updated_fields)}")
                else:
                    logger.info(f"No updates needed for @{candidate.handle}")
            
            db.commit()

        search = DiscoverySearch()
        _, _, matches = search.search(request.description, request.constraints, top_k=20)
        _store_results(db, request, matches)

        request.status = RequestStatus.DONE
        db.commit()
        logger.info("Discovery job completed: request_id=%s", request_id)
    except Exception:
        request = db.get(Request, request_id)
        if request:
            request.status = RequestStatus.FAILED
            db.commit()
        logger.exception("Discovery job failed: request_id=%s", request_id)
        raise
    finally:
        db.close()


def _store_results(db, request: Request, matches: list[dict]) -> None:
    db.query(RequestResult).filter(RequestResult.request_id == request.id).delete()
    db.commit()

    for rank, match in enumerate(matches, start=1):
        handle = match.get("id") or match.get("metadata", {}).get("handle")
        if not handle:
            continue
        influencer = db.execute(select(Influencer).where(Influencer.handle == handle)).scalar_one_or_none()
        if not influencer:
            meta = match.get("metadata", {})
            influencer = Influencer(
                handle=handle,
                name=meta.get("name", ""),
                bio=meta.get("bio", ""),
                profile_summary=meta.get("profile_summary", ""),
                category=meta.get("category", ""),
                tags=meta.get("tags", ""),
                followers=meta.get("followers", 0),
                avg_likes=meta.get("avg_likes", 0),
                avg_comments=meta.get("avg_comments", 0),
                profile_url=meta.get("profile_url", ""),
                platform="instagram",
                country=meta.get("country", ""),
                gender=meta.get("gender", ""),
            )
            db.add(influencer)
            db.commit()

        result = RequestResult(
            request_id=request.id,
            influencer_id=influencer.id,
            score=float(match.get("score", 0)),
            rank=rank,
        )
        db.add(result)
    db.commit()


# ======= Reddit Lead Generation Tasks =======

@celery_app.task(name="app.workers.tasks.poll_reddit_scheduled")
def poll_reddit_scheduled() -> dict:
    """
    Tier-based scheduled Reddit polling task.

    Runs every hour and checks which users should be polled based on their tier:
    - Starter plans: 2x/day at UTC 07:00 and 16:00
    - Growth/Pro plans: 4x/day at UTC 07:00, 11:00, 16:00, 22:00

    This task respects the ENABLE_SCHEDULED_POLLING setting.
    """
    from app.services.reddit.scheduler import run_scheduled_polls

    logger.info("Starting tier-based scheduled Reddit polling")

    try:
        stats = run_scheduled_polls()
        logger.info(f"Scheduled Reddit polling complete: {stats}")
        return stats

    except Exception as e:
        logger.exception("Scheduled Reddit polling task failed")
        raise


@celery_app.task(name="app.workers.tasks.poll_reddit_leads")
def poll_reddit_leads() -> dict:
    """
    Legacy: Centralized Reddit polling task (polls all active campaigns)
    Kept for backward compatibility.
    """
    db = SessionLocal()
    try:
        logger.info("Starting Reddit polling task (legacy)")

        polling_service = RedditPollingService()
        summary = polling_service.poll_all_active_subreddits(db)

        logger.info(f"Reddit polling complete: {summary}")
        return summary

    except Exception as e:
        logger.exception("Reddit polling task failed")
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.poll_campaign_first")
def poll_campaign_first(campaign_id: int) -> dict:
    """
    Run the first poll for a newly created campaign.
    Called via Celery in production.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting first poll for campaign {campaign_id} (Celery task)")

        polling_service = RedditPollingService()
        summary = polling_service.poll_campaign_immediately(db, campaign_id)

        logger.info(f"First poll completed for campaign {campaign_id}: {summary}")
        return summary

    except Exception as e:
        logger.exception(f"First poll failed for campaign {campaign_id}")
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.poll_campaign_background", bind=True)
def poll_campaign_background(self, campaign_id: int) -> dict:
    """
    Background Celery task for polling a campaign.

    Stores progress in Redis so frontend can poll for updates.
    Continues running even if user closes the page.

    Progress format:
    {
        "task_id": "...",
        "status": "running" | "completed" | "failed",
        "phase": "fetching" | "scoring" | "suggestions" | "saving",
        "current": 5,
        "total": 10,
        "message": "Fetching posts from r/startups...",
        "leads_created": 0,
        "leads": [...],  # List of lead IDs created
        "error": null
    }
    """
    import asyncio
    from app.services.reddit.streaming_poll import StreamingPollService

    db = SessionLocal()
    task_id = self.request.id

    try:
        logger.info(f"Starting background poll for campaign {campaign_id}, task_id={task_id}")

        # Initialize status
        set_poll_task_status(campaign_id, {
            "task_id": task_id,
            "status": "running",
            "phase": "initializing",
            "current": 0,
            "total": 0,
            "message": "Initializing polling...",
            "leads_created": 0,
            "leads": [],
            "error": None,
            "started_at": datetime.utcnow().isoformat()
        })

        service = StreamingPollService()
        leads_created = []
        final_result = {}

        # Run the async generator synchronously
        async def run_poll():
            nonlocal leads_created, final_result

            async for event in service.poll_campaign_streaming(db, campaign_id):
                event_type = event["type"]
                event_data = event["data"]

                if event_type == "progress":
                    set_poll_task_status(campaign_id, {
                        "task_id": task_id,
                        "status": "running",
                        "phase": event_data.get("phase", "processing"),
                        "current": event_data.get("current", 0),
                        "total": event_data.get("total", 0),
                        "message": event_data.get("message", ""),
                        "leads_created": len(leads_created),
                        "leads": leads_created,
                        "error": None,
                        "started_at": get_poll_task_status(campaign_id).get("started_at")
                    })

                elif event_type == "lead":
                    leads_created.append(event_data.get("id"))
                    current_status = get_poll_task_status(campaign_id) or {}
                    set_poll_task_status(campaign_id, {
                        **current_status,
                        "leads_created": len(leads_created),
                        "leads": leads_created,
                    })

                elif event_type == "complete":
                    final_result = event_data

                elif event_type == "error":
                    raise Exception(event_data.get("message", "Unknown error"))

        # Run the async function
        asyncio.run(run_poll())

        # Set final completed status
        set_poll_task_status(campaign_id, {
            "task_id": task_id,
            "status": "completed",
            "phase": "done",
            "current": final_result.get("total_posts_fetched", 0),
            "total": final_result.get("total_posts_fetched", 0),
            "message": final_result.get("message", "Polling completed"),
            "leads_created": final_result.get("total_leads", len(leads_created)),
            "leads": leads_created,
            "error": None,
            "completed_at": datetime.utcnow().isoformat(),
            "summary": final_result
        })

        logger.info(f"Background poll completed for campaign {campaign_id}: {len(leads_created)} leads")
        return {"status": "completed", "leads_created": len(leads_created)}

    except Exception as e:
        logger.exception(f"Background poll failed for campaign {campaign_id}")

        # Set error status
        current_status = get_poll_task_status(campaign_id) or {}
        set_poll_task_status(campaign_id, {
            **current_status,
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })

        raise
    finally:
        db.close()
