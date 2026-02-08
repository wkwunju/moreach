"""
Reddit Scheduled Polling Service

Handles scheduled polling based on user subscription tiers:
- Starter plans: 2x/day (UTC 07:00, 16:00)
- Growth/Pro plans: 4x/day (UTC 07:00, 11:00, 16:00, 22:00)

This service should be called by a cron job or scheduler every hour.
"""
import logging
from datetime import datetime, timezone
from typing import List, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.email import send_poll_summary_email
from app.models.tables import (
    User,
    RedditCampaign,
    RedditCampaignStatus,
    RedditLead,
    SubscriptionTier,
)
from app.services.reddit.polling import RedditPollingService


logger = logging.getLogger(__name__)


# Tier classification
STARTER_TIERS = {
    SubscriptionTier.STARTER_MONTHLY,
    SubscriptionTier.STARTER_ANNUALLY,
}

PREMIUM_TIERS = {
    SubscriptionTier.GROWTH_MONTHLY,
    SubscriptionTier.GROWTH_ANNUALLY,
    SubscriptionTier.PRO_MONTHLY,
    SubscriptionTier.PRO_ANNUALLY,
    # Legacy tiers treated as premium
    SubscriptionTier.MONTHLY,
    SubscriptionTier.ANNUALLY,
}

# Free trial also gets starter-level polling
FREE_TRIAL_TIERS = {
    SubscriptionTier.FREE_TRIAL,
}


def get_poll_hours_for_tier(tier: SubscriptionTier) -> Set[int]:
    """
    Get the UTC hours when polling should run for a given tier.

    Returns:
        Set of UTC hour values (0-23)
    """
    if tier in PREMIUM_TIERS:
        # Growth/Pro: 4x/day
        hours_str = settings.POLL_TIMES_PREMIUM
    elif tier in STARTER_TIERS or tier in FREE_TRIAL_TIERS:
        # Starter/Trial: 2x/day
        hours_str = settings.POLL_TIMES_STARTER
    else:
        # Expired or unknown: no polling
        return set()

    try:
        return {int(h.strip()) for h in hours_str.split(",")}
    except ValueError:
        logger.error(f"Invalid poll times configuration: {hours_str}")
        return set()


def should_poll_now(tier: SubscriptionTier, current_hour: int) -> bool:
    """
    Check if polling should run now for a given tier.

    Args:
        tier: User's subscription tier
        current_hour: Current UTC hour (0-23)

    Returns:
        True if polling should run
    """
    poll_hours = get_poll_hours_for_tier(tier)
    return current_hour in poll_hours


def run_scheduled_polls(current_hour: int = None) -> dict:
    """
    Run scheduled polls for all eligible users.

    This function should be called every hour by a scheduler.
    It will check each user's tier and poll their campaigns if it's
    their scheduled time.

    Args:
        current_hour: Override current hour for testing (default: use actual UTC hour)

    Returns:
        Summary dict with stats
    """
    if not settings.ENABLE_SCHEDULED_POLLING:
        logger.info("Scheduled polling is disabled")
        return {"status": "disabled", "message": "Scheduled polling is disabled"}

    if current_hour is None:
        current_hour = datetime.now(timezone.utc).hour

    logger.info(f"Running scheduled polls for UTC hour {current_hour}")

    db = SessionLocal()
    polling_service = RedditPollingService()

    stats = {
        "hour": current_hour,
        "users_checked": 0,
        "campaigns_polled": 0,
        "campaigns_skipped": 0,
        "errors": 0,
    }

    try:
        # Get all users with active campaigns
        users_with_campaigns = db.execute(
            select(User)
            .join(RedditCampaign, RedditCampaign.user_id == User.id)
            .where(RedditCampaign.status == RedditCampaignStatus.ACTIVE)
            .distinct()
        ).scalars().all()

        logger.info(f"Found {len(users_with_campaigns)} users with active campaigns")

        for user in users_with_campaigns:
            stats["users_checked"] += 1

            # Check if this user should be polled at this hour
            if not should_poll_now(user.subscription_tier, current_hour):
                logger.debug(
                    f"Skipping user {user.id} ({user.subscription_tier.value}): "
                    f"not scheduled for hour {current_hour}"
                )
                continue

            # Get all active campaigns for this user
            campaigns = db.execute(
                select(RedditCampaign)
                .where(
                    RedditCampaign.user_id == user.id,
                    RedditCampaign.status == RedditCampaignStatus.ACTIVE
                )
            ).scalars().all()

            for campaign in campaigns:
                try:
                    logger.info(
                        f"Polling campaign {campaign.id} for user {user.id} "
                        f"(tier: {user.subscription_tier.value})"
                    )
                    summary = polling_service.poll_campaign_immediately(db, campaign.id)
                    stats["campaigns_polled"] += 1
                    logger.info(f"Campaign {campaign.id} poll completed: {summary}")

                    # Send email notification if leads were created
                    leads_created = summary.get("total_leads_created", 0)
                    if leads_created > 0 and user.email:
                        try:
                            # Get top leads for this campaign (sorted by score)
                            top_leads_query = db.query(RedditLead).filter(
                                RedditLead.campaign_id == campaign.id
                            ).order_by(RedditLead.relevancy_score.desc()).limit(10).all()

                            top_leads = [
                                {
                                    "title": lead.title,
                                    "subreddit_name": lead.subreddit_name,
                                    "relevancy_score": lead.relevancy_score,
                                    "post_url": lead.post_url
                                }
                                for lead in top_leads_query
                            ]

                            high_quality_count = sum(
                                1 for lead in top_leads_query
                                if lead.relevancy_score is not None and lead.relevancy_score >= 80
                            )

                            send_poll_summary_email(
                                to_email=user.email,
                                campaign_name=campaign.business_description[:100],
                                total_posts_fetched=summary.get("total_posts_found", 0),
                                total_leads_created=leads_created,
                                high_quality_count=high_quality_count,
                                top_leads=top_leads,
                                campaign_id=campaign.id
                            )
                            logger.info(f"Sent poll summary email to {user.email}")

                        except Exception as email_error:
                            logger.error(f"Error sending email for campaign {campaign.id}: {email_error}")

                except Exception as e:
                    logger.error(
                        f"Error polling campaign {campaign.id}: {e}",
                        exc_info=True
                    )
                    stats["errors"] += 1

    except Exception as e:
        logger.error(f"Error in scheduled polling: {e}", exc_info=True)
        stats["errors"] += 1

    finally:
        db.close()

    logger.info(f"Scheduled polling complete: {stats}")
    return stats


def get_polling_schedule_info(tier: SubscriptionTier) -> dict:
    """
    Get polling schedule information for a given tier.

    Args:
        tier: User's subscription tier

    Returns:
        Dict with schedule info for display to user
    """
    poll_hours = get_poll_hours_for_tier(tier)

    if not poll_hours:
        return {
            "enabled": False,
            "polls_per_day": 0,
            "times_utc": [],
            "description": "No scheduled polling (subscription required)"
        }

    polls_per_day = len(poll_hours)
    times_utc = sorted(poll_hours)

    # Format times for display
    time_strings = [f"{h:02d}:00 UTC" for h in times_utc]

    if polls_per_day == 2:
        description = "2x daily: Europe morning (8am CET) & US West Coast morning (8am PST)"
    else:
        description = "4x daily: comprehensive global coverage"

    return {
        "enabled": True,
        "polls_per_day": polls_per_day,
        "times_utc": times_utc,
        "times_formatted": time_strings,
        "description": description
    }


# CLI entry point for running via cron
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Allow passing hour as argument for testing
    hour = int(sys.argv[1]) if len(sys.argv) > 1 else None

    result = run_scheduled_polls(current_hour=hour)
    print(f"Scheduled polling result: {result}")
