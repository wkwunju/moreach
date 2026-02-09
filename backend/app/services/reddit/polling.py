"""
Reddit Polling Service

Provides:
1. poll_campaign_immediately() - delegates to unified PollEngine
2. Centralized polling helpers (get_subreddits_to_poll, poll_subreddit, poll_all_active_subreddits)
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    RedditCampaign,
    RedditCampaignSubreddit,
    RedditLead,
    RedditLeadStatus,
    GlobalSubredditPoll,
    RedditCampaignStatus,
    APIType
)
from app.providers.reddit.factory import get_reddit_provider
from app.services.usage_tracking import track_api_call
from app.core.config import settings
from app.core.plan_limits import get_plan_limits


logger = logging.getLogger(__name__)


class RedditPollingService:
    """
    Reddit polling service.
    Campaign-specific polling delegates to the unified PollEngine.
    Centralized polling helpers remain for legacy compatibility.
    """

    def __init__(self):
        self.reddit_provider = get_reddit_provider()

    def poll_campaign_immediately(
        self, db: Session, campaign_id: int, trigger: str = "manual"
    ) -> Dict[str, Any]:
        """
        Poll a specific campaign's subreddits immediately.
        Delegates to the unified PollEngine.

        Args:
            db: Database session
            campaign_id: Campaign to poll
            trigger: "manual" | "scheduled" | "first_poll"

        Returns:
            Summary statistics
        """
        from app.services.reddit.poll_engine import run_poll_sync

        logger.info(f"Starting immediate poll for campaign {campaign_id}")
        poll_job = run_poll_sync(db, campaign_id, trigger=trigger)

        summary = {
            "campaign_id": campaign_id,
            "poll_job_id": poll_job.id,
            "subreddits_polled": poll_job.subreddits_polled,
            "total_posts_found": poll_job.posts_fetched,
            "total_leads_created": poll_job.leads_created,
        }

        logger.info(f"Immediate poll complete for campaign {campaign_id}: {summary}")
        return summary

    # ====================================================================
    # Centralized polling helpers (legacy path for poll_all_active_subreddits)
    # ====================================================================

    def get_subreddits_to_poll(self, db: Session, max_age_hours: int = 6) -> List[str]:
        """
        Get list of subreddits that need polling.

        Strategy:
        1. Find all active campaigns
        2. Collect all their subreddits
        3. Deduplicate
        4. Filter out recently polled ones
        """
        active_campaigns = db.execute(
            select(RedditCampaign).where(
                RedditCampaign.status == RedditCampaignStatus.ACTIVE
            )
        ).scalars().all()

        if not active_campaigns:
            logger.info("No active campaigns found")
            return []

        all_subreddits = set()
        for campaign in active_campaigns:
            for sub in campaign.subreddits:
                if sub.is_active:
                    all_subreddits.add(sub.subreddit_name)

        logger.info(f"Found {len(all_subreddits)} unique subreddits across {len(active_campaigns)} campaigns")

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        subreddits_to_poll = []

        for subreddit_name in all_subreddits:
            poll_record = db.execute(
                select(GlobalSubredditPoll).where(
                    GlobalSubredditPoll.subreddit_name == subreddit_name
                )
            ).scalar_one_or_none()

            if poll_record is None:
                subreddits_to_poll.append(subreddit_name)
            elif poll_record.last_poll_at < cutoff_time:
                subreddits_to_poll.append(subreddit_name)
            else:
                logger.debug(f"Skipping r/{subreddit_name} - recently polled")

        logger.info(f"{len(subreddits_to_poll)} subreddits need polling")
        return subreddits_to_poll

    def poll_subreddit(
        self,
        db: Session,
        subreddit_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Poll a single subreddit for new posts using Apify Reddit Scraper.
        Updates GlobalSubredditPoll tracking.
        """
        logger.info(f"Polling r/{subreddit_name}")

        poll_record = db.execute(
            select(GlobalSubredditPoll).where(
                GlobalSubredditPoll.subreddit_name == subreddit_name
            )
        ).scalar_one_or_none()

        time_filter = "day"
        since_timestamp = None

        if poll_record and poll_record.last_poll_at:
            hours_since_last_poll = (datetime.utcnow() - poll_record.last_poll_at).total_seconds() / 3600

            if hours_since_last_poll <= 1:
                time_filter = "hour"
            elif hours_since_last_poll <= 24:
                time_filter = "day"
            elif hours_since_last_poll <= 168:
                time_filter = "week"
            elif hours_since_last_poll <= 720:
                time_filter = "month"
            else:
                time_filter = "year"

            since_timestamp = poll_record.last_post_timestamp
            logger.info(f"Last polled {hours_since_last_poll:.1f}h ago, using time_filter='{time_filter}'")
        else:
            since_timestamp = (datetime.utcnow() - timedelta(hours=24)).timestamp()
            logger.info(f"First poll for r/{subreddit_name}, using time_filter='day'")

        all_posts = self.reddit_provider.scrape_subreddit(
            subreddit_name=subreddit_name,
            max_posts=limit,
            sort="new",
            time_filter=time_filter
        )

        posts = all_posts

        logger.info(f"Found {len(posts)} posts in r/{subreddit_name} from Apify (time_filter='{time_filter}')")

        if poll_record:
            poll_record.last_poll_at = datetime.utcnow()
            poll_record.poll_count += 1
            poll_record.total_posts_found += len(posts)
            if posts:
                poll_record.last_post_timestamp = max(p["created_utc"] for p in posts if p["created_utc"])
        else:
            poll_record = GlobalSubredditPoll(
                subreddit_name=subreddit_name,
                last_poll_at=datetime.utcnow(),
                last_post_timestamp=max(p["created_utc"] for p in posts if p["created_utc"]) if posts else since_timestamp,
                poll_count=1,
                total_posts_found=len(posts)
            )
            db.add(poll_record)

        db.commit()

        return posts

    def distribute_leads(
        self,
        db: Session,
        subreddit_name: str,
        posts: List[Dict[str, Any]]
    ) -> int:
        """
        Distribute posts to relevant campaigns as leads (centralized polling path).
        Uses PollEngine per-campaign for consistent scoring.
        """
        if not posts:
            return 0

        campaigns = db.execute(
            select(RedditCampaign).join(
                RedditCampaignSubreddit,
                RedditCampaignSubreddit.campaign_id == RedditCampaign.id
            ).where(
                RedditCampaign.status == RedditCampaignStatus.ACTIVE,
                RedditCampaignSubreddit.subreddit_name == subreddit_name,
                RedditCampaignSubreddit.is_active == True
            )
        ).scalars().all()

        if not campaigns:
            logger.info(f"No active campaigns for r/{subreddit_name}")
            return 0

        logger.info(f"Distributing {len(posts)} posts to {len(campaigns)} campaigns")

        total_leads = 0
        for campaign in campaigns:
            try:
                summary = self.poll_campaign_immediately(
                    db, campaign.id, trigger="scheduled"
                )
                total_leads += summary.get("total_leads_created", 0)
            except Exception as e:
                logger.error(f"Error distributing to campaign {campaign.id}: {e}", exc_info=True)
                db.rollback()

        return total_leads

    def poll_all_active_subreddits(self, db: Session) -> Dict[str, Any]:
        """
        Main polling function: Poll all active subreddits and distribute leads.
        Called by Celery task.
        """
        logger.info("Starting centralized Reddit polling")

        subreddits_to_poll = self.get_subreddits_to_poll(db)

        if not subreddits_to_poll:
            logger.info("No subreddits need polling")
            return {
                "subreddits_polled": 0,
                "total_posts_found": 0,
                "total_leads_created": 0
            }

        total_posts = 0
        total_leads = 0

        for subreddit_name in subreddits_to_poll:
            try:
                posts = self.poll_subreddit(db, subreddit_name)
                total_posts += len(posts)

                leads_created = self.distribute_leads(db, subreddit_name, posts)
                total_leads += leads_created

            except Exception as e:
                logger.error(f"Error polling r/{subreddit_name}: {e}", exc_info=True)
                db.rollback()
                continue

        summary = {
            "subreddits_polled": len(subreddits_to_poll),
            "total_posts_found": total_posts,
            "total_leads_created": total_leads
        }

        logger.info(f"Polling complete: {summary}")
        return summary
