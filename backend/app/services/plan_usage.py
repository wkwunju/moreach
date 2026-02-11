"""
Plan usage checking service.

Checks user's current usage against their plan limits and determines
if they need to upgrade to perform certain actions.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.tables import User, RedditCampaign, RedditCampaignSubreddit, RedditCampaignStatus
from app.core.plan_limits import get_plan_limits, get_tier_group, PlanLimits


logger = logging.getLogger(__name__)


@dataclass
class UsageStatus:
    """Current usage status for a user"""
    # Current counts
    profile_count: int
    max_profiles: int

    # Plan info
    current_plan: str
    tier_group: str
    next_tier: Optional[str]

    # Computed flags
    can_create_profile: bool
    profiles_remaining: int


@dataclass
class SubredditLimitStatus:
    """Subreddit limit status for a campaign"""
    current_count: int
    max_count: int
    can_add_more: bool
    remaining: int
    current_plan: str
    tier_group: str
    next_tier: Optional[str]


@dataclass
class LimitCheckResult:
    """Result of a limit check"""
    allowed: bool
    reason: Optional[str] = None
    current_count: int = 0
    max_count: int = 0
    upgrade_to: Optional[str] = None
    current_plan: str = ""


def get_user_profile_count(db: Session, user_id: int) -> int:
    """Get the number of active profiles (campaigns) for a user"""
    count = db.execute(
        select(func.count(RedditCampaign.id)).where(
            RedditCampaign.user_id == user_id,
            RedditCampaign.status != RedditCampaignStatus.DELETED
        )
    ).scalar()
    return count or 0


def get_campaign_subreddit_count(db: Session, campaign_id: int) -> int:
    """Get the number of subreddits for a campaign"""
    count = db.execute(
        select(func.count(RedditCampaignSubreddit.id)).where(
            RedditCampaignSubreddit.campaign_id == campaign_id,
            RedditCampaignSubreddit.is_active == True
        )
    ).scalar()
    return count or 0


def get_usage_status(db: Session, user: User) -> UsageStatus:
    """Get the current usage status for a user"""
    limits = get_plan_limits(user.subscription_tier, user_id=user.id)
    tier_group = get_tier_group(user.subscription_tier)
    profile_count = get_user_profile_count(db, user.id)

    can_create = profile_count < limits.max_profiles
    remaining = max(0, limits.max_profiles - profile_count)

    return UsageStatus(
        profile_count=profile_count,
        max_profiles=limits.max_profiles,
        current_plan=limits.plan_name,
        tier_group=tier_group,
        next_tier=limits.next_tier,
        can_create_profile=can_create,
        profiles_remaining=remaining,
    )


def get_subreddit_limit_status(db: Session, user: User, campaign_id: int) -> SubredditLimitStatus:
    """Get the subreddit limit status for a campaign"""
    limits = get_plan_limits(user.subscription_tier, user_id=user.id)
    tier_group = get_tier_group(user.subscription_tier)
    current_count = get_campaign_subreddit_count(db, campaign_id)

    can_add = current_count < limits.max_subreddits_per_profile
    remaining = max(0, limits.max_subreddits_per_profile - current_count)

    return SubredditLimitStatus(
        current_count=current_count,
        max_count=limits.max_subreddits_per_profile,
        can_add_more=can_add,
        remaining=remaining,
        current_plan=limits.plan_name,
        tier_group=tier_group,
        next_tier=limits.next_tier,
    )


def check_can_create_profile(db: Session, user: User) -> LimitCheckResult:
    """
    Check if user can create a new business profile.

    Returns:
        LimitCheckResult with allowed=True if user can create,
        or allowed=False with reason and upgrade info if not.
    """
    limits = get_plan_limits(user.subscription_tier, user_id=user.id)
    tier_group = get_tier_group(user.subscription_tier)
    profile_count = get_user_profile_count(db, user.id)

    if profile_count >= limits.max_profiles:
        return LimitCheckResult(
            allowed=False,
            reason=f"You've reached the maximum of {limits.max_profiles} business profile(s) on the {limits.plan_name} plan.",
            current_count=profile_count,
            max_count=limits.max_profiles,
            upgrade_to=limits.next_tier,
            current_plan=limits.plan_name,
        )

    return LimitCheckResult(
        allowed=True,
        current_count=profile_count,
        max_count=limits.max_profiles,
        current_plan=limits.plan_name,
    )


def check_can_add_subreddits(
    db: Session,
    user: User,
    campaign_id: int,
    new_subreddit_count: int
) -> LimitCheckResult:
    """
    Check if user can add more subreddits to a campaign.

    Args:
        db: Database session
        user: Current user
        campaign_id: Campaign to add subreddits to
        new_subreddit_count: Number of new subreddits to add

    Returns:
        LimitCheckResult with allowed=True if user can add,
        or allowed=False with reason and upgrade info if not.
    """
    limits = get_plan_limits(user.subscription_tier, user_id=user.id)
    tier_group = get_tier_group(user.subscription_tier)
    current_count = get_campaign_subreddit_count(db, campaign_id)

    total_after_add = current_count + new_subreddit_count

    if total_after_add > limits.max_subreddits_per_profile:
        return LimitCheckResult(
            allowed=False,
            reason=f"This would exceed the {limits.max_subreddits_per_profile} subreddit limit on the {limits.plan_name} plan.",
            current_count=current_count,
            max_count=limits.max_subreddits_per_profile,
            upgrade_to=limits.next_tier,
            current_plan=limits.plan_name,
        )

    return LimitCheckResult(
        allowed=True,
        current_count=current_count,
        max_count=limits.max_subreddits_per_profile,
        current_plan=limits.plan_name,
    )


def check_subreddit_selection(
    db: Session,
    user: User,
    campaign_id: int,
    selected_count: int
) -> LimitCheckResult:
    """
    Check if the selected number of subreddits is within limits.
    This is for new selections (replacing existing subreddits).

    Args:
        db: Database session
        user: Current user
        campaign_id: Campaign ID
        selected_count: Number of subreddits user wants to select

    Returns:
        LimitCheckResult
    """
    limits = get_plan_limits(user.subscription_tier, user_id=user.id)

    if selected_count > limits.max_subreddits_per_profile:
        return LimitCheckResult(
            allowed=False,
            reason=f"You can only select up to {limits.max_subreddits_per_profile} subreddits on the {limits.plan_name} plan.",
            current_count=selected_count,
            max_count=limits.max_subreddits_per_profile,
            upgrade_to=limits.next_tier,
            current_plan=limits.plan_name,
        )

    return LimitCheckResult(
        allowed=True,
        current_count=selected_count,
        max_count=limits.max_subreddits_per_profile,
        current_plan=limits.plan_name,
    )
