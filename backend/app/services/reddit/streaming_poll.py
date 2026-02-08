"""
Streaming Reddit Polling Service

SSE-enabled polling service that yields events during the polling process.
Used for real-time progress updates to the frontend.
"""
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    RedditCampaign,
    RedditLead,
    RedditLeadStatus,
    GlobalSubredditPoll,
    RedditCampaignStatus,
    User,
    APIType
)
from app.providers.reddit.factory import get_reddit_provider
from app.services.reddit.batch_scoring import BatchScoringService, AUTO_SUGGESTION_THRESHOLD
from app.core.email import send_poll_summary_email
from app.services.usage_tracking import track_api_call
from app.core.config import settings
from app.core.plan_limits import get_plan_limits


logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_POSTS_PER_SUBREDDIT = 20
DEFAULT_TOP_N_SUGGESTIONS = 20
MIN_RELEVANCY_SCORE = 50


class StreamingPollService:
    """
    Streaming poll service that yields SSE events during polling

    Event types:
    - progress: {"phase": "fetching"|"scoring"|"suggestions", "current": N, "total": M, ...}
    - lead: {"id": N, "title": "...", "relevancy_score": 90, ...}
    - complete: {"total_leads": N, "total_posts_fetched": M, "summary": {...}}
    - error: {"message": "..."}
    """

    def __init__(self):
        self.reddit_provider = get_reddit_provider()
        self.scoring_service = BatchScoringService()

    async def poll_campaign_streaming(
        self,
        db: Session,
        campaign_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Poll campaign with streaming progress updates

        Yields SSE events throughout the process:
        1. Fetching posts from subreddits
        2. Batch quick scoring
        3. Generating suggestions for top N
        4. Saving leads to database
        5. Sending email notification
        """
        try:
            # Get campaign and validate
            campaign = db.get(RedditCampaign, campaign_id)
            if not campaign:
                yield {"type": "error", "data": {"message": f"Campaign {campaign_id} not found"}}
                return

            if campaign.status != RedditCampaignStatus.ACTIVE:
                yield {"type": "error", "data": {"message": f"Campaign is not active (status: {campaign.status})"}}
                return

            # Get active subreddits
            active_subreddits = [sub for sub in campaign.subreddits if sub.is_active]
            if not active_subreddits:
                yield {"type": "error", "data": {"message": "No active subreddits in this campaign"}}
                return

            # Smart budget: calculate posts per subreddit based on tier
            user = db.get(User, campaign.user_id)
            plan_limits = get_plan_limits(user.subscription_tier) if user else None
            if plan_limits and plan_limits.max_posts_per_poll > 0:
                posts_per_sub = max(5, plan_limits.max_posts_per_poll // len(active_subreddits))
            else:
                posts_per_sub = DEFAULT_POSTS_PER_SUBREDDIT

            logger.info(
                f"Smart budget: {len(active_subreddits)} subreddits × {posts_per_sub} posts "
                f"(tier budget: {plan_limits.max_posts_per_poll if plan_limits else 'N/A'})"
            )

            # ============================================
            # Phase 1: Fetch posts from all subreddits
            # ============================================
            yield {
                "type": "progress",
                "data": {
                    "phase": "fetching",
                    "current": 0,
                    "total": len(active_subreddits),
                    "message": "Starting to fetch posts..."
                }
            }

            all_posts = []
            subreddit_post_counts = {}

            for i, sub in enumerate(active_subreddits):
                try:
                    # Fetch posts (run sync Apify call in thread pool)
                    posts = await asyncio.to_thread(
                        self.reddit_provider.scrape_subreddit,
                        subreddit_name=sub.subreddit_name,
                        max_posts=posts_per_sub,
                        sort="new",
                        time_filter="day"
                    )

                    # Filter out duplicates (posts already in this campaign)
                    existing_post_ids = set(
                        row[0] for row in db.execute(
                            select(RedditLead.reddit_post_id).where(
                                RedditLead.campaign_id == campaign_id
                            )
                        ).fetchall()
                    )

                    new_posts = [p for p in posts if p.get("id") not in existing_post_ids]
                    all_posts.extend(new_posts)
                    subreddit_post_counts[sub.subreddit_name] = len(new_posts)

                    # Track Reddit API usage
                    reddit_api_type = APIType.REDDIT_RAPIDAPI if settings.reddit_api_provider.lower() == "rapidapi" else APIType.REDDIT_APIFY
                    track_api_call(db, campaign.user_id, reddit_api_type)

                    yield {
                        "type": "progress",
                        "data": {
                            "phase": "fetching",
                            "current": i + 1,
                            "total": len(active_subreddits),
                            "subreddit": sub.subreddit_name,
                            "posts_found": len(new_posts),
                            "message": f"Fetched {len(new_posts)} new posts from r/{sub.subreddit_name}"
                        }
                    }

                    # Update global poll record
                    await self._update_poll_record(db, sub.subreddit_name, len(posts))

                except Exception as e:
                    logger.error(f"Error fetching r/{sub.subreddit_name}: {e}")
                    yield {
                        "type": "progress",
                        "data": {
                            "phase": "fetching",
                            "current": i + 1,
                            "total": len(active_subreddits),
                            "subreddit": sub.subreddit_name,
                            "error": str(e),
                            "message": f"Error fetching r/{sub.subreddit_name}: {str(e)}"
                        }
                    }

            if not all_posts:
                yield {
                    "type": "complete",
                    "data": {
                        "total_leads": 0,
                        "total_posts_fetched": 0,
                        "message": "No new posts found"
                    }
                }
                return

            # ============================================
            # Phase 2: Batch quick scoring
            # ============================================
            yield {
                "type": "progress",
                "data": {
                    "phase": "scoring",
                    "current": 0,
                    "total": len(all_posts),
                    "message": f"Scoring {len(all_posts)} posts..."
                }
            }

            # Track scoring progress
            scoring_progress = {"current": 0}

            def on_scoring_progress(current: int, total: int):
                scoring_progress["current"] = current

            # Run batch scoring
            scored_posts = await self.scoring_service.batch_quick_score(
                all_posts,
                campaign.business_description,
                on_progress=on_scoring_progress
            )

            # Track LLM usage for scoring (actual number of batch calls made)
            llm_calls = self.scoring_service.get_llm_calls_made()
            if llm_calls > 0:
                llm_type = APIType.LLM_GEMINI if settings.llm_provider.lower() == "gemini" else APIType.LLM_OPENAI
                for _ in range(llm_calls):
                    track_api_call(db, campaign.user_id, llm_type)
                logger.info(f"Tracked {llm_calls} LLM calls for batch scoring")

            yield {
                "type": "progress",
                "data": {
                    "phase": "scoring",
                    "current": len(scored_posts),
                    "total": len(scored_posts),
                    "message": f"Scored {len(scored_posts)} posts"
                }
            }

            # Filter to keep only relevant posts (score >= 50)
            relevant_posts = [p for p in scored_posts if p.get("relevancy_score", 0) >= MIN_RELEVANCY_SCORE]

            # ============================================
            # Phase 3: Auto-generate suggestions for 90+ score posts only
            # Other posts get suggestions on-demand when user clicks
            # ============================================
            high_score_posts = [p for p in relevant_posts if p.get("relevancy_score", 0) >= AUTO_SUGGESTION_THRESHOLD]

            if high_score_posts:
                yield {
                    "type": "progress",
                    "data": {
                        "phase": "suggestions",
                        "current": 0,
                        "total": len(high_score_posts),
                        "message": f"Auto-generating suggestions for {len(high_score_posts)} high-score (90+) posts..."
                    }
                }

                # Generate suggestions only for 90+ score posts
                scored_posts = await self.scoring_service.generate_suggestions_for_high_score(
                    relevant_posts,
                    campaign.business_description,
                    min_score=AUTO_SUGGESTION_THRESHOLD
                )

                yield {
                    "type": "progress",
                    "data": {
                        "phase": "suggestions",
                        "current": len(high_score_posts),
                        "total": len(high_score_posts),
                        "message": f"Auto-generated suggestions for {len(high_score_posts)} high-score posts"
                    }
                }
            else:
                logger.info("No posts scored 90+, skipping auto-suggestion generation")

            # ============================================
            # Phase 4: Save leads to database
            # ============================================
            leads_created = 0
            relevancy_distribution = {"90+": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0}
            saved_leads = []  # Track saved leads for email

            for scored_post in relevant_posts:
                try:
                    lead = RedditLead(
                        campaign_id=campaign_id,
                        reddit_post_id=scored_post["id"],
                        subreddit_name=scored_post.get("subreddit_name", ""),
                        title=scored_post["title"],
                        content=scored_post.get("content", ""),
                        author=scored_post.get("author", "[deleted]"),
                        post_url=scored_post.get("url", ""),
                        score=scored_post.get("score", 0),
                        num_comments=scored_post.get("num_comments", 0),
                        created_utc=scored_post.get("created_utc", 0),
                        relevancy_score=scored_post["relevancy_score"],
                        relevancy_reason=scored_post.get("relevancy_reason", ""),
                        suggested_comment=scored_post.get("suggested_comment", ""),
                        suggested_dm=scored_post.get("suggested_dm", ""),
                        has_suggestions=scored_post.get("has_suggestions", False),
                        status=RedditLeadStatus.NEW
                    )
                    db.add(lead)
                    db.flush()  # Get ID without committing

                    leads_created += 1

                    # Track distribution and save lead data for email
                    score = scored_post["relevancy_score"]
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

                    # Save lead data for email (top leads)
                    saved_leads.append({
                        "title": lead.title,
                        "subreddit_name": lead.subreddit_name,
                        "relevancy_score": lead.relevancy_score,
                        "post_url": lead.post_url
                    })

                    # Yield lead event
                    yield {
                        "type": "lead",
                        "data": {
                            "id": lead.id,
                            "title": lead.title[:100],
                            "relevancy_score": lead.relevancy_score,
                            "subreddit_name": lead.subreddit_name,
                            "has_suggestions": lead.has_suggestions,
                            "author": lead.author
                        }
                    }

                except Exception as e:
                    logger.error(f"Error saving lead {scored_post.get('id')}: {e}")
                    db.rollback()

            # Commit all leads
            db.commit()

            # Update campaign last_poll_at
            campaign.last_poll_at = datetime.utcnow()
            db.commit()

            # ============================================
            # Phase 5: Send email notification
            # ============================================
            try:
                # Get user email
                user = db.get(User, campaign.user_id)
                if user and user.email:
                    # Sort leads by score and get top 10
                    top_leads = sorted(saved_leads, key=lambda x: -x["relevancy_score"])[:10]
                    high_quality_count = relevancy_distribution.get("90+", 0) + relevancy_distribution.get("80-89", 0)

                    await asyncio.to_thread(
                        send_poll_summary_email,
                        to_email=user.email,
                        campaign_name=campaign.business_description[:100],
                        total_posts_fetched=len(all_posts),
                        total_leads_created=leads_created,
                        high_quality_count=high_quality_count,
                        top_leads=top_leads,
                        campaign_id=campaign_id
                    )
                    logger.info(f"Sent poll summary email to {user.email}")
            except Exception as e:
                logger.error(f"Error sending email: {e}")

            # ============================================
            # Final: Send complete event
            # ============================================
            yield {
                "type": "complete",
                "data": {
                    "total_leads": leads_created,
                    "total_posts_fetched": len(all_posts),
                    "subreddits_polled": len(active_subreddits),
                    "relevancy_distribution": relevancy_distribution,
                    "subreddit_distribution": subreddit_post_counts,
                    "message": f"Created {leads_created} new leads from {len(all_posts)} posts"
                }
            }

        except Exception as e:
            logger.error(f"Error in streaming poll: {e}", exc_info=True)
            yield {"type": "error", "data": {"message": str(e)}}

    async def _update_poll_record(self, db: Session, subreddit_name: str, posts_count: int):
        """Update or create GlobalSubredditPoll record"""
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
                    total_posts_found=posts_count
                )
                db.add(poll_record)

            db.commit()
        except Exception as e:
            logger.error(f"Error updating poll record for r/{subreddit_name}: {e}")
            db.rollback()


# Synchronous wrapper for non-SSE usage
def poll_campaign_with_batch_scoring(db: Session, campaign_id: int) -> Dict[str, Any]:
    """
    Non-streaming version of the batch scoring poll
    Used for background tasks or non-SSE endpoints
    """
    service = StreamingPollService()

    # Collect all events and return final summary
    async def collect_events():
        final_result = {}
        async for event in service.poll_campaign_streaming(db, campaign_id):
            if event["type"] == "complete":
                final_result = event["data"]
            elif event["type"] == "error":
                raise Exception(event["data"]["message"])
        return final_result

    return asyncio.run(collect_events())
