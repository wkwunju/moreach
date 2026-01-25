import logging
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.tables import Request, Influencer, RequestResult, RequestStatus
from app.services.discovery.pipeline import DiscoveryPipeline
from app.services.discovery.search import DiscoverySearch
from app.services.reddit.polling import RedditPollingService
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


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

@celery_app.task(name="app.workers.tasks.poll_reddit_leads")
def poll_reddit_leads() -> dict:
    """
    Centralized Reddit polling task
    Runs periodically (e.g., every 6 hours) to poll all active subreddits
    """
    db = SessionLocal()
    try:
        logger.info("Starting Reddit polling task")
        
        polling_service = RedditPollingService()
        summary = polling_service.poll_all_active_subreddits(db)
        
        logger.info(f"Reddit polling complete: {summary}")
        return summary
        
    except Exception as e:
        logger.exception("Reddit polling task failed")
        raise
    finally:
        db.close()
