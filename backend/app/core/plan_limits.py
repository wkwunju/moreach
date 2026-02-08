"""
Plan limits configuration for subscription tiers.

Defines the resource limits for each subscription tier:
- Business profiles (campaigns)
- Subreddits per campaign
- Leads per month
- Polling frequency
"""

from dataclasses import dataclass
from typing import Optional
from app.models.tables import SubscriptionTier


@dataclass
class PlanLimits:
    """Resource limits for a subscription plan"""
    max_profiles: int  # Max business profiles (campaigns)
    max_subreddits_per_profile: int  # Max subreddits per campaign
    max_leads_per_month: int  # Max leads per month
    polls_per_day: int  # How many times per day we poll
    max_posts_per_poll: int  # Max total posts to fetch per poll cycle (budget)
    plan_name: str  # Display name
    next_tier: Optional[str] = None  # Tier to upgrade to


# Plan limits configuration
PLAN_LIMITS = {
    # Trial and Starter have the same limits - both upgrade to Growth
    # max_posts_per_poll: 150 budget → e.g. 15 subreddits × 10 posts each
    SubscriptionTier.FREE_TRIAL: PlanLimits(
        max_profiles=1,
        max_subreddits_per_profile=15,
        max_leads_per_month=3000,
        polls_per_day=2,
        max_posts_per_poll=150,
        plan_name="Starter",
        next_tier="GROWTH",
    ),
    SubscriptionTier.STARTER_MONTHLY: PlanLimits(
        max_profiles=1,
        max_subreddits_per_profile=15,
        max_leads_per_month=3000,
        polls_per_day=2,
        max_posts_per_poll=150,
        plan_name="Starter",
        next_tier="GROWTH",
    ),
    SubscriptionTier.STARTER_ANNUALLY: PlanLimits(
        max_profiles=1,
        max_subreddits_per_profile=15,
        max_leads_per_month=3000,
        polls_per_day=2,
        max_posts_per_poll=150,
        plan_name="Starter",
        next_tier="GROWTH",
    ),
    # Growth tier - more generous budget
    SubscriptionTier.GROWTH_MONTHLY: PlanLimits(
        max_profiles=3,
        max_subreddits_per_profile=20,
        max_leads_per_month=9000,
        polls_per_day=24,
        max_posts_per_poll=300,
        plan_name="Growth",
        next_tier="PRO",
    ),
    SubscriptionTier.GROWTH_ANNUALLY: PlanLimits(
        max_profiles=3,
        max_subreddits_per_profile=20,
        max_leads_per_month=9000,
        polls_per_day=24,
        max_posts_per_poll=300,
        plan_name="Growth",
        next_tier="PRO",
    ),
    # Pro tier - highest budget
    SubscriptionTier.PRO_MONTHLY: PlanLimits(
        max_profiles=10,
        max_subreddits_per_profile=999,
        max_leads_per_month=30000,
        polls_per_day=24,
        max_posts_per_poll=500,
        plan_name="Pro",
        next_tier=None,
    ),
    SubscriptionTier.PRO_ANNUALLY: PlanLimits(
        max_profiles=10,
        max_subreddits_per_profile=999,
        max_leads_per_month=30000,
        polls_per_day=24,
        max_posts_per_poll=500,
        plan_name="Pro",
        next_tier=None,
    ),
    # Legacy tiers (same as Starter)
    SubscriptionTier.MONTHLY: PlanLimits(
        max_profiles=1,
        max_subreddits_per_profile=15,
        max_leads_per_month=3000,
        polls_per_day=2,
        max_posts_per_poll=150,
        plan_name="Starter",
        next_tier="GROWTH",
    ),
    SubscriptionTier.ANNUALLY: PlanLimits(
        max_profiles=1,
        max_subreddits_per_profile=15,
        max_leads_per_month=3000,
        polls_per_day=2,
        max_posts_per_poll=150,
        plan_name="Starter",
        next_tier="GROWTH",
    ),
    # Expired - no access
    SubscriptionTier.EXPIRED: PlanLimits(
        max_profiles=0,
        max_subreddits_per_profile=0,
        max_leads_per_month=0,
        polls_per_day=0,
        max_posts_per_poll=0,
        plan_name="Expired",
        next_tier="STARTER",
    ),
}


def get_plan_limits(tier: SubscriptionTier) -> PlanLimits:
    """Get the limits for a subscription tier"""
    return PLAN_LIMITS.get(tier, PLAN_LIMITS[SubscriptionTier.FREE_TRIAL])


def get_tier_group(tier: SubscriptionTier) -> str:
    """Get the tier group name (STARTER, GROWTH, PRO)"""
    tier_str = tier.value
    if "STARTER" in tier_str or tier_str in ("FREE_TRIAL", "MONTHLY", "ANNUALLY"):
        return "STARTER"
    elif "GROWTH" in tier_str:
        return "GROWTH"
    elif "PRO" in tier_str:
        return "PRO"
    return "EXPIRED"
