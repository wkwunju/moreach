"""
Stripe Billing Service

Handles checkout sessions, webhooks, and subscription management.
"""

import stripe
import logging
from datetime import datetime
from typing import Optional, Literal

from app.core.config import settings
from app.models.tables import User, SubscriptionTier
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Price ID mapping
PRICE_ID_MAP = {
    "STARTER_MONTHLY": settings.STRIPE_PRICE_STARTER_MONTHLY,
    "STARTER_ANNUALLY": settings.STRIPE_PRICE_STARTER_ANNUALLY,
    "GROWTH_MONTHLY": settings.STRIPE_PRICE_GROWTH_MONTHLY,
    "GROWTH_ANNUALLY": settings.STRIPE_PRICE_GROWTH_ANNUALLY,
    "PRO_MONTHLY": settings.STRIPE_PRICE_PRO_MONTHLY,
    "PRO_ANNUALLY": settings.STRIPE_PRICE_PRO_ANNUALLY,
}

# Reverse mapping: price_id -> tier
TIER_FROM_PRICE = {v: k for k, v in PRICE_ID_MAP.items() if v}


def get_or_create_customer(user: User, db: Session) -> str:
    """Get existing Stripe customer or create a new one."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    # Create new customer
    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name or user.email,
        metadata={
            "user_id": str(user.id),
        }
    )

    # Save customer ID to user
    user.stripe_customer_id = customer.id
    db.commit()

    logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
    return customer.id


def create_checkout_session(
    user: User,
    tier_code: str,
    db: Session,
    success_url: str,
    cancel_url: str,
) -> dict:
    """
    Create a Stripe Checkout Session for subscription.

    Args:
        user: The user subscribing
        tier_code: e.g., "STARTER_MONTHLY", "GROWTH_ANNUALLY"
        db: Database session
        success_url: URL to redirect on success
        cancel_url: URL to redirect on cancel

    Returns:
        dict with checkout_url
    """
    price_id = PRICE_ID_MAP.get(tier_code)
    if not price_id:
        raise ValueError(f"Invalid tier code: {tier_code}")

    customer_id = get_or_create_customer(user, db)

    # Determine if this is a trial-eligible plan (Starter only)
    is_starter = tier_code.startswith("STARTER")
    is_trial_eligible = is_starter and user.subscription_tier == SubscriptionTier.FREE_TRIAL

    session_params = {
        "mode": "subscription",
        "customer": customer_id,
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "user_id": str(user.id),
            "tier_code": tier_code,
        },
        "subscription_data": {
            "metadata": {
                "user_id": str(user.id),
                "tier_code": tier_code,
            }
        },
        "allow_promotion_codes": True,
    }

    # Add trial period for Starter plan if user hasn't had a paid subscription
    if is_trial_eligible:
        session_params["subscription_data"]["trial_period_days"] = 7

    session = stripe.checkout.Session.create(**session_params)

    logger.info(f"Created checkout session {session.id} for user {user.id}, tier {tier_code}")

    return {
        "checkout_url": session.url,
        "session_id": session.id,
    }


def create_customer_portal_session(user: User, db: Session, return_url: str) -> dict:
    """
    Create a Stripe Customer Portal session for managing subscriptions.
    """
    if not user.stripe_customer_id:
        raise ValueError("User has no Stripe customer ID")

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=return_url,
    )

    return {
        "portal_url": session.url,
    }


def handle_checkout_completed(session: stripe.checkout.Session, db: Session) -> None:
    """Handle successful checkout completion."""
    user_id = session.metadata.get("user_id")
    tier_code = session.metadata.get("tier_code")
    subscription_id = session.subscription

    if not user_id or not tier_code:
        logger.error(f"Missing metadata in checkout session {session.id}")
        return

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        logger.error(f"User {user_id} not found for checkout session {session.id}")
        return

    # Update user subscription
    try:
        new_tier = SubscriptionTier(tier_code)
    except ValueError:
        logger.error(f"Invalid tier code {tier_code}")
        return

    user.subscription_tier = new_tier
    user.stripe_subscription_id = subscription_id
    user.trial_ends_at = None  # Clear trial since they're now subscribed

    # Get subscription details for end date
    if subscription_id:
        subscription = stripe.Subscription.retrieve(subscription_id)
        user.subscription_ends_at = datetime.fromtimestamp(subscription.current_period_end)

    db.commit()
    logger.info(f"User {user_id} subscribed to {tier_code}")


def handle_subscription_updated(subscription: stripe.Subscription, db: Session) -> None:
    """Handle subscription updates (upgrades, downgrades, renewals)."""
    user_id = subscription.metadata.get("user_id")
    tier_code = subscription.metadata.get("tier_code")

    if not user_id:
        # Try to find user by customer ID
        customer_id = subscription.customer
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.error(f"No user found for subscription {subscription.id}")
            return
    else:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.error(f"User {user_id} not found for subscription {subscription.id}")
            return

    # Determine tier from price ID if not in metadata
    if not tier_code and subscription.items.data:
        price_id = subscription.items.data[0].price.id
        tier_code = TIER_FROM_PRICE.get(price_id)

    if tier_code:
        try:
            user.subscription_tier = SubscriptionTier(tier_code)
        except ValueError:
            logger.error(f"Invalid tier code {tier_code}")

    user.stripe_subscription_id = subscription.id
    user.subscription_ends_at = datetime.fromtimestamp(subscription.current_period_end)

    # Handle subscription status
    if subscription.status == "active":
        user.trial_ends_at = None
    elif subscription.status == "trialing":
        if subscription.trial_end:
            user.trial_ends_at = datetime.fromtimestamp(subscription.trial_end)

    db.commit()
    logger.info(f"Updated subscription for user {user.id}: {tier_code}, status={subscription.status}")


def handle_subscription_deleted(subscription: stripe.Subscription, db: Session) -> None:
    """Handle subscription cancellation."""
    customer_id = subscription.customer
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

    if not user:
        logger.error(f"No user found for cancelled subscription {subscription.id}")
        return

    user.subscription_tier = SubscriptionTier.EXPIRED
    user.stripe_subscription_id = None
    user.subscription_ends_at = datetime.utcnow()

    db.commit()
    logger.info(f"Subscription cancelled for user {user.id}")


def handle_invoice_payment_failed(invoice: stripe.Invoice, db: Session) -> None:
    """Handle failed payment."""
    customer_id = invoice.customer
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

    if not user:
        logger.error(f"No user found for failed invoice {invoice.id}")
        return

    # Log the failure but don't immediately expire - Stripe will retry
    logger.warning(f"Payment failed for user {user.id}, invoice {invoice.id}")

    # TODO: Send notification email to user about payment failure
