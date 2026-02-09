"""
Unified Reddit Poll Engine

Single source of truth for the polling pipeline used by both
frontend (SSE streaming) and backend (scheduler) paths:

  1. Create PollJob record
  2. Fetch posts from subreddits
  3. Save posts to DB (with poll_job_id, score=NULL)
  4. Batch score all posts
  5. Delete unscored / low-score posts
  6. Generate suggestions for high-score posts (90+)
  7. Update PollJob stats and mark complete
  8. Send email using ONLY this job's leads
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    RedditCampaign,
    RedditLead,
    RedditLeadStatus,
    GlobalSubredditPoll,
    RedditCampaignStatus,
    PollJob,
    PollJobStatus,
    User,
    APIType,
    SubscriptionTier,
)
from app.providers.reddit.factory import get_reddit_provider
from app.services.reddit.batch_scoring import BatchScoringService, AUTO_SUGGESTION_THRESHOLD
from app.core.email import send_poll_summary_email
from app.services.usage_tracking import track_api_call
from app.core.config import settings
from app.core.plan_limits import get_plan_limits


logger = logging.getLogger(__name__)

# Configuration
DEFAULT_POSTS_PER_SUBREDDIT = 20
MIN_RELEVANCY_SCORE = 50


class PollEngineCallbacks:
    """
    Callback interface for consumers that want progress updates.
    The streaming path subclasses this; sync callers use the default no-op.
    """

    async def on_progress(self, phase: str, current: int, total: int,
                          message: str, **extra) -> None:
        pass

    async def on_lead_created(self, lead: RedditLead) -> None:
        pass

    async def on_complete(self, stats: Dict[str, Any]) -> None:
        pass

    async def on_error(self, message: str) -> None:
        pass


class PollEngine:
    """Unified polling engine used by all polling paths."""

    def __init__(self):
        self.reddit_provider = get_reddit_provider()
        self.scoring_service = BatchScoringService()

    async def run_poll(
        self,
        db: Session,
        campaign_id: int,
        trigger: str = "manual",
        callbacks: Optional[PollEngineCallbacks] = None,
    ) -> PollJob:
        """
        Execute the full polling pipeline for a campaign.

        Args:
            db: Database session
            campaign_id: Campaign to poll
            trigger: "manual" | "scheduled" | "first_poll"
            callbacks: Optional callbacks for progress updates (SSE streaming)

        Returns:
            The completed PollJob record
        """
        if callbacks is None:
            callbacks = PollEngineCallbacks()

        # --- Validate campaign ---
        campaign = db.get(RedditCampaign, campaign_id)
        if not campaign:
            await callbacks.on_error(f"Campaign {campaign_id} not found")
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != RedditCampaignStatus.ACTIVE:
            await callbacks.on_error(f"Campaign is not active (status: {campaign.status})")
            raise ValueError(f"Campaign {campaign_id} is not active (status: {campaign.status})")

        # --- Validate user ---
        user = db.get(User, campaign.user_id)
        if not user:
            await callbacks.on_error(f"User {campaign.user_id} not found")
            raise ValueError(f"User {campaign.user_id} not found")

        if not user.is_active:
            await callbacks.on_error(f"User {user.id} account is deactivated")
            raise ValueError(f"User {user.id} account is deactivated")

        if user.is_blocked:
            await callbacks.on_error(f"User {user.id} account is blocked")
            raise ValueError(f"User {user.id} account is blocked")

        if user.subscription_tier == SubscriptionTier.EXPIRED:
            await callbacks.on_error(f"User {user.id} subscription has expired")
            raise ValueError(f"User {user.id} subscription has expired")

        # Check if subscription/trial has actually expired by date
        now = datetime.utcnow()
        if (user.subscription_tier == SubscriptionTier.FREE_TRIAL
                and user.trial_ends_at and user.trial_ends_at < now):
            await callbacks.on_error(f"User {user.id} free trial has ended")
            raise ValueError(f"User {user.id} free trial has ended")

        if (user.subscription_tier != SubscriptionTier.FREE_TRIAL
                and user.subscription_ends_at and user.subscription_ends_at < now):
            await callbacks.on_error(f"User {user.id} subscription has ended")
            raise ValueError(f"User {user.id} subscription has ended")

        active_subreddits = [sub for sub in campaign.subreddits if sub.is_active]
        if not active_subreddits:
            await callbacks.on_error("No active subreddits in this campaign")
            raise ValueError("No active subreddits in this campaign")

        # --- Create PollJob ---
        poll_job = PollJob(
            campaign_id=campaign_id,
            status=PollJobStatus.RUNNING,
            trigger=trigger,
        )
        db.add(poll_job)
        db.commit()
        db.refresh(poll_job)

        try:
            # --- Phase 1: Fetch posts ---
            all_posts, subreddit_post_counts = await self._fetch_posts(
                db, campaign, active_subreddits, poll_job, callbacks
            )

            if not all_posts:
                poll_job.status = PollJobStatus.COMPLETED
                poll_job.completed_at = datetime.utcnow()
                db.commit()
                stats = {
                    "total_leads": 0,
                    "total_posts_fetched": 0,
                    "subreddits_polled": len(active_subreddits),
                    "message": "No new posts found"
                }
                await callbacks.on_complete(stats)
                return poll_job

            poll_job.posts_fetched = len(all_posts)
            poll_job.subreddits_polled = len(active_subreddits)
            db.commit()

            # --- Phase 2: Save unscored leads ---
            new_leads = self._save_unscored_leads(db, campaign_id, poll_job.id, all_posts)

            # --- Phase 3: Batch score ---
            await self._batch_score_leads(db, campaign, poll_job, new_leads, callbacks)

            # --- Phase 4: Cleanup low-score / unscored leads ---
            self._cleanup_low_score_leads(db, poll_job)

            # --- Emit lead events for surviving leads ---
            surviving_leads = db.execute(
                select(RedditLead).where(
                    RedditLead.poll_job_id == poll_job.id
                )
            ).scalars().all()
            for lead in surviving_leads:
                await callbacks.on_lead_created(lead)

            # --- Phase 5: Generate suggestions for 90+ ---
            await self._generate_suggestions(db, campaign, poll_job, callbacks)

            # --- Phase 6: Finalize job ---
            poll_job.status = PollJobStatus.COMPLETED
            poll_job.completed_at = datetime.utcnow()

            # Update campaign last_poll_at
            campaign.last_poll_at = datetime.utcnow()
            db.commit()

            # --- Phase 7: Send email ---
            await self._send_email(db, campaign, poll_job)

            # --- Complete ---
            # Recount final leads for this job
            final_leads = db.execute(
                select(RedditLead).where(
                    RedditLead.poll_job_id == poll_job.id
                )
            ).scalars().all()

            relevancy_distribution = {"90+": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0}
            for lead in final_leads:
                score = lead.relevancy_score or 0
                if score >= 90:
                    relevancy_distribution["90+"] += 1
                elif score >= 80:
                    relevancy_distribution["80-89"] += 1
                elif score >= 70:
                    relevancy_distribution["70-79"] += 1
                elif score >= 60:
                    relevancy_distribution["60-69"] += 1
                else:
                    relevancy_distribution["50-59"] += 1

            stats = {
                "total_leads": poll_job.leads_created,
                "total_posts_fetched": poll_job.posts_fetched,
                "subreddits_polled": poll_job.subreddits_polled,
                "relevancy_distribution": relevancy_distribution,
                "subreddit_distribution": subreddit_post_counts,
                "message": f"Created {poll_job.leads_created} new leads from {poll_job.posts_fetched} posts"
            }
            await callbacks.on_complete(stats)
            return poll_job

        except Exception as e:
            logger.error(f"Error in poll engine: {e}", exc_info=True)
            poll_job.status = PollJobStatus.FAILED
            poll_job.error_message = str(e)
            poll_job.completed_at = datetime.utcnow()
            db.commit()
            await callbacks.on_error(str(e))
            raise

    async def _fetch_posts(
        self,
        db: Session,
        campaign: RedditCampaign,
        active_subreddits: list,
        poll_job: PollJob,
        callbacks: PollEngineCallbacks,
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Phase 1: Fetch posts from all active subreddits."""
        user = db.get(User, campaign.user_id)
        plan_limits = get_plan_limits(user.subscription_tier) if user else None
        if plan_limits and plan_limits.max_posts_per_poll > 0:
            posts_per_sub = max(5, plan_limits.max_posts_per_poll // len(active_subreddits))
        else:
            posts_per_sub = DEFAULT_POSTS_PER_SUBREDDIT

        logger.info(
            f"Smart budget: {len(active_subreddits)} subreddits x {posts_per_sub} posts "
            f"(tier budget: {plan_limits.max_posts_per_poll if plan_limits else 'N/A'})"
        )

        await callbacks.on_progress(
            phase="fetching", current=0, total=len(active_subreddits),
            message="Starting to fetch posts..."
        )

        all_posts: List[Dict[str, Any]] = []
        subreddit_post_counts: Dict[str, int] = {}

        # Get existing post IDs for deduplication
        existing_post_ids = set(
            row[0] for row in db.execute(
                select(RedditLead.reddit_post_id).where(
                    RedditLead.campaign_id == campaign.id
                )
            ).fetchall()
        )

        for i, sub in enumerate(active_subreddits):
            try:
                posts = await asyncio.to_thread(
                    self.reddit_provider.scrape_subreddit,
                    subreddit_name=sub.subreddit_name,
                    max_posts=posts_per_sub,
                    sort="new",
                    time_filter="day"
                )

                new_posts = [p for p in posts if p.get("id") not in existing_post_ids]
                all_posts.extend(new_posts)
                subreddit_post_counts[sub.subreddit_name] = len(new_posts)

                # Also add new IDs to dedup set for cross-subreddit dedup
                for p in new_posts:
                    existing_post_ids.add(p.get("id"))

                # Track Reddit API usage
                reddit_api_type = (
                    APIType.REDDIT_RAPIDAPI
                    if settings.reddit_api_provider.lower() == "rapidapi"
                    else APIType.REDDIT_APIFY
                )
                track_api_call(db, campaign.user_id, reddit_api_type)

                await callbacks.on_progress(
                    phase="fetching", current=i + 1, total=len(active_subreddits),
                    subreddit=sub.subreddit_name, posts_found=len(new_posts),
                    message=f"Fetched {len(new_posts)} new posts from r/{sub.subreddit_name}"
                )

                # Update global poll record
                await self._update_poll_record(db, sub.subreddit_name, len(posts))

            except Exception as e:
                logger.error(f"Error fetching r/{sub.subreddit_name}: {e}")
                await callbacks.on_progress(
                    phase="fetching", current=i + 1, total=len(active_subreddits),
                    subreddit=sub.subreddit_name, error=str(e),
                    message=f"Error fetching r/{sub.subreddit_name}: {str(e)}"
                )

        return all_posts, subreddit_post_counts

    def _save_unscored_leads(
        self,
        db: Session,
        campaign_id: int,
        poll_job_id: int,
        posts: List[Dict[str, Any]],
    ) -> List[RedditLead]:
        """Phase 2: Save all new posts with score=NULL, linked to poll_job."""
        new_leads = []
        for post in posts:
            try:
                lead = RedditLead(
                    campaign_id=campaign_id,
                    poll_job_id=poll_job_id,
                    reddit_post_id=post.get("id", ""),
                    subreddit_name=post.get("subreddit_name", ""),
                    title=post.get("title", ""),
                    content=post.get("content", ""),
                    author=post.get("author", "[deleted]"),
                    post_url=post.get("url", ""),
                    score=post.get("score", 0),
                    num_comments=post.get("num_comments", 0),
                    created_utc=post.get("created_utc", 0),
                    relevancy_score=None,
                    relevancy_reason="Pending scoring",
                    suggested_comment="",
                    suggested_dm="",
                    status=RedditLeadStatus.NEW,
                )
                db.add(lead)
                new_leads.append(lead)
            except Exception as e:
                logger.error(f"Error saving post {post.get('id')}: {e}")
                continue

        db.commit()
        logger.info(f"Saved {len(new_leads)} unscored leads for poll_job {poll_job_id}")
        return new_leads

    async def _batch_score_leads(
        self,
        db: Session,
        campaign: RedditCampaign,
        poll_job: PollJob,
        leads: List[RedditLead],
        callbacks: PollEngineCallbacks,
    ) -> None:
        """Phase 3: Batch score all leads using BatchScoringService."""
        if not leads:
            return

        await callbacks.on_progress(
            phase="scoring", current=0, total=len(leads),
            message=f"Scoring {len(leads)} posts..."
        )

        # Build post dicts for the batch scorer
        post_dicts = []
        for lead in leads:
            post_dicts.append({
                "id": lead.reddit_post_id,
                "reddit_post_id": lead.reddit_post_id,
                "title": lead.title,
                "content": lead.content,
                "author": lead.author,
                "url": lead.post_url,
                "score": lead.score,
                "num_comments": lead.num_comments,
                "created_utc": lead.created_utc,
                "subreddit_name": lead.subreddit_name,
            })

        # Run batch scoring
        scored_posts = await self.scoring_service.batch_quick_score(
            post_dicts, campaign.business_description
        )

        # Track LLM usage
        llm_calls = self.scoring_service.get_llm_calls_made()
        if llm_calls > 0:
            llm_type = (
                APIType.LLM_GEMINI
                if settings.llm_provider.lower() == "gemini"
                else APIType.LLM_OPENAI
            )
            for _ in range(llm_calls):
                track_api_call(db, campaign.user_id, llm_type)
            logger.info(f"Tracked {llm_calls} LLM calls for batch scoring")

        # Build a map from post_id to scored result
        scores_map: Dict[str, Dict] = {}
        for sp in scored_posts:
            pid = sp.get("reddit_post_id") or sp.get("id", "")
            scores_map[pid] = sp

        # Update leads with scores
        scored_count = 0
        for lead in leads:
            scored = scores_map.get(lead.reddit_post_id)
            if scored:
                lead.relevancy_score = scored.get("relevancy_score")
                lead.relevancy_reason = scored.get("relevancy_reason", "")
                scored_count += 1
            else:
                # Not returned by scorer - leave as NULL
                lead.relevancy_reason = "Score not returned by batch scorer"

        poll_job.posts_scored = scored_count
        db.commit()

        await callbacks.on_progress(
            phase="scoring", current=len(leads), total=len(leads),
            message=f"Scored {scored_count} posts"
        )

        logger.info(f"Batch scored {scored_count}/{len(leads)} leads")

    def _cleanup_low_score_leads(self, db: Session, poll_job: PollJob) -> None:
        """Phase 4: Delete leads with score < 50 or still NULL."""
        leads = db.execute(
            select(RedditLead).where(
                RedditLead.poll_job_id == poll_job.id
            )
        ).scalars().all()

        kept = 0
        deleted = 0
        for lead in leads:
            if lead.relevancy_score is None or lead.relevancy_score < MIN_RELEVANCY_SCORE:
                db.delete(lead)
                deleted += 1
            else:
                kept += 1

        poll_job.leads_created = kept
        poll_job.leads_deleted = deleted
        db.commit()

        logger.info(f"Cleanup: kept {kept}, deleted {deleted} leads for poll_job {poll_job.id}")

    async def _generate_suggestions(
        self,
        db: Session,
        campaign: RedditCampaign,
        poll_job: PollJob,
        callbacks: PollEngineCallbacks,
    ) -> None:
        """Phase 5: Generate suggestions for top N 90+ score leads (capped by plan)."""
        high_score_leads = db.execute(
            select(RedditLead).where(
                RedditLead.poll_job_id == poll_job.id,
                RedditLead.relevancy_score >= AUTO_SUGGESTION_THRESHOLD
            ).order_by(RedditLead.relevancy_score.desc())
        ).scalars().all()

        if not high_score_leads:
            logger.info("No posts scored 90+, skipping auto-suggestion generation")
            return

        # Cap by plan limits to control LLM costs
        user = db.get(User, campaign.user_id)
        plan_limits = get_plan_limits(user.subscription_tier) if user else None
        max_suggestions = plan_limits.max_auto_suggestions if plan_limits else 5
        if len(high_score_leads) > max_suggestions:
            logger.info(
                f"Capping auto-suggestions from {len(high_score_leads)} to {max_suggestions} "
                f"(plan: {plan_limits.plan_name if plan_limits else 'default'}). "
                f"Rest available on-demand."
            )
            high_score_leads = high_score_leads[:max_suggestions]

        await callbacks.on_progress(
            phase="suggestions", current=0, total=len(high_score_leads),
            message=f"Auto-generating suggestions for {len(high_score_leads)} high-score (90+) posts..."
        )

        # Build post dicts for suggestion generation
        post_dicts = []
        for lead in high_score_leads:
            post_dicts.append({
                "id": lead.reddit_post_id,
                "reddit_post_id": lead.reddit_post_id,
                "title": lead.title,
                "content": lead.content,
                "author": lead.author,
                "subreddit_name": lead.subreddit_name,
                "relevancy_score": lead.relevancy_score,
                "relevancy_reason": lead.relevancy_reason,
            })

        # Generate suggestions via batch service
        results = await self.scoring_service.generate_suggestions_for_high_score(
            post_dicts,
            campaign.business_description,
            min_score=AUTO_SUGGESTION_THRESHOLD
        )

        # Update leads with suggestions
        suggestions_count = 0
        results_map: Dict[str, Dict] = {}
        for r in results:
            pid = r.get("reddit_post_id") or r.get("id", "")
            results_map[pid] = r

        for lead in high_score_leads:
            result = results_map.get(lead.reddit_post_id)
            if result and result.get("has_suggestions"):
                lead.suggested_comment = result.get("suggested_comment", "")
                lead.suggested_dm = result.get("suggested_dm", "")
                lead.has_suggestions = True
                lead.suggestions_generated_at = datetime.utcnow()
                suggestions_count += 1

        poll_job.suggestions_generated = suggestions_count
        db.commit()

        await callbacks.on_progress(
            phase="suggestions", current=len(high_score_leads), total=len(high_score_leads),
            message=f"Auto-generated suggestions for {suggestions_count} high-score posts"
        )

        logger.info(f"Generated suggestions for {suggestions_count}/{len(high_score_leads)} leads")

    async def _send_email(
        self,
        db: Session,
        campaign: RedditCampaign,
        poll_job: PollJob,
    ) -> None:
        """Phase 7: Send email notification scoped to this job's leads."""
        try:
            user = db.get(User, campaign.user_id)
            if not user or not user.email:
                return

            if poll_job.leads_created == 0:
                return

            # Query leads specifically for this poll job
            top_leads_query = db.execute(
                select(RedditLead).where(
                    RedditLead.poll_job_id == poll_job.id,
                    RedditLead.relevancy_score.isnot(None),
                ).order_by(RedditLead.relevancy_score.desc()).limit(10)
            ).scalars().all()

            top_leads = [
                {
                    "title": lead.title,
                    "subreddit_name": lead.subreddit_name,
                    "relevancy_score": lead.relevancy_score,
                    "post_url": lead.post_url,
                }
                for lead in top_leads_query
            ]

            high_quality_count = sum(
                1 for lead in top_leads_query
                if lead.relevancy_score is not None and lead.relevancy_score >= 80
            )

            await asyncio.to_thread(
                send_poll_summary_email,
                to_email=user.email,
                campaign_name=campaign.business_description[:100],
                total_posts_fetched=poll_job.posts_fetched,
                total_leads_created=poll_job.leads_created,
                high_quality_count=high_quality_count,
                top_leads=top_leads,
                campaign_id=campaign.id,
            )
            logger.info(f"Sent poll summary email to {user.email}")

        except Exception as e:
            logger.error(f"Error sending email for campaign {campaign.id}: {e}")

    async def _update_poll_record(
        self, db: Session, subreddit_name: str, posts_count: int
    ) -> None:
        """Update or create GlobalSubredditPoll record."""
        try:
            poll_record = db.execute(
                select(GlobalSubredditPoll).where(
                    GlobalSubredditPoll.subreddit_name == subreddit_name
                )
            ).scalar_one_or_none()

            if poll_record:
                poll_record.last_poll_at = datetime.utcnow()
                poll_record.poll_count += 1
                poll_record.total_posts_found += posts_count
            else:
                poll_record = GlobalSubredditPoll(
                    subreddit_name=subreddit_name,
                    last_poll_at=datetime.utcnow(),
                    poll_count=1,
                    total_posts_found=posts_count,
                )
                db.add(poll_record)

            db.commit()
        except Exception as e:
            logger.error(f"Error updating poll record for r/{subreddit_name}: {e}")
            db.rollback()


def run_poll_sync(
    db: Session,
    campaign_id: int,
    trigger: str = "manual",
) -> PollJob:
    """Synchronous wrapper for non-async contexts."""
    engine = PollEngine()
    return asyncio.run(engine.run_poll(db, campaign_id, trigger))
