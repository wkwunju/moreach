"""
Tests for Stripe billing functionality.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.tables import User, SubscriptionTier
from app.services.stripe_billing import (
    get_or_create_customer,
    create_checkout_session,
    create_customer_portal_session,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_payment_failed,
    PRICE_ID_MAP,
    TIER_FROM_PRICE,
)


class TestStripeCustomer:
    """Tests for Stripe customer management."""

    def test_get_existing_customer(self, db: Session, test_user_paid: User):
        """Test getting existing customer returns existing ID."""
        customer_id = get_or_create_customer(test_user_paid, db)
        assert customer_id == test_user_paid.stripe_customer_id

    def test_create_new_customer(self, db: Session, test_user: User, mock_stripe):
        """Test creating new customer for user without one."""
        # Ensure no customer ID
        assert test_user.stripe_customer_id is None

        customer_id = get_or_create_customer(test_user, db)

        assert customer_id == "cus_test_new"
        db.refresh(test_user)
        assert test_user.stripe_customer_id == "cus_test_new"


class TestCheckoutSession:
    """Tests for checkout session creation."""

    def test_create_checkout_session_starter(self, db: Session, test_user: User, mock_stripe):
        """Test creating checkout session for Starter plan."""
        with patch("app.services.stripe_billing.settings.STRIPE_PRICE_STARTER_MONTHLY", "price_starter_monthly"):
            result = create_checkout_session(
                user=test_user,
                tier_code="STARTER_MONTHLY",
                db=db,
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel",
            )

        assert "checkout_url" in result
        assert result["checkout_url"] == "https://checkout.stripe.com/test"

    def test_create_checkout_session_growth(self, db: Session, test_user: User, mock_stripe):
        """Test creating checkout session for Growth plan."""
        with patch("app.services.stripe_billing.settings.STRIPE_PRICE_GROWTH_ANNUALLY", "price_growth_annually"):
            result = create_checkout_session(
                user=test_user,
                tier_code="GROWTH_ANNUALLY",
                db=db,
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel",
            )

        assert "checkout_url" in result

    def test_create_checkout_invalid_tier(self, db: Session, test_user: User):
        """Test creating checkout with invalid tier fails."""
        with pytest.raises(ValueError, match="Invalid tier code"):
            create_checkout_session(
                user=test_user,
                tier_code="INVALID_TIER",
                db=db,
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel",
            )

    def test_create_checkout_trial_eligibility(self, db: Session, test_user: User, mock_stripe):
        """Test trial period is added for Starter plan on FREE_TRIAL users."""
        with patch("app.services.stripe_billing.settings.STRIPE_PRICE_STARTER_MONTHLY", "price_starter_monthly"):
            create_checkout_session(
                user=test_user,
                tier_code="STARTER_MONTHLY",
                db=db,
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel",
            )

        # Check that trial_period_days was passed
        call_kwargs = mock_stripe["checkout"].call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7


class TestCustomerPortal:
    """Tests for customer portal session."""

    def test_create_portal_session(self, db: Session, test_user_paid: User, mock_stripe):
        """Test creating customer portal session."""
        result = create_customer_portal_session(
            user=test_user_paid,
            db=db,
            return_url="http://localhost:3000/reddit",
        )

        assert "portal_url" in result
        assert result["portal_url"] == "https://billing.stripe.com/test"

    def test_create_portal_no_customer(self, db: Session, test_user: User):
        """Test portal creation fails without customer ID."""
        with pytest.raises(ValueError, match="no Stripe customer ID"):
            create_customer_portal_session(
                user=test_user,
                db=db,
                return_url="http://localhost:3000/reddit",
            )


class TestWebhookHandlers:
    """Tests for Stripe webhook event handlers."""

    def test_handle_checkout_completed(self, db: Session, test_user: User, mock_stripe):
        """Test checkout.session.completed webhook handler."""
        # Mock the Stripe session object
        mock_session = MagicMock()
        mock_session.metadata = {
            "user_id": str(test_user.id),
            "tier_code": "STARTER_MONTHLY",
        }
        mock_session.subscription = "sub_test_123"
        mock_session.id = "cs_test_123"

        handle_checkout_completed(mock_session, db)

        db.refresh(test_user)
        assert test_user.subscription_tier == SubscriptionTier.STARTER_MONTHLY
        assert test_user.stripe_subscription_id == "sub_test_123"
        assert test_user.trial_ends_at is None

    def test_handle_subscription_updated(self, db: Session, test_user_paid: User):
        """Test customer.subscription.updated webhook handler."""
        mock_subscription = MagicMock()
        mock_subscription.metadata = {"user_id": str(test_user_paid.id)}
        mock_subscription.id = "sub_updated_123"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        mock_subscription.items.data = []

        handle_subscription_updated(mock_subscription, db)

        db.refresh(test_user_paid)
        assert test_user_paid.stripe_subscription_id == "sub_updated_123"

    def test_handle_subscription_deleted(self, db: Session, test_user_paid: User):
        """Test customer.subscription.deleted webhook handler."""
        mock_subscription = MagicMock()
        mock_subscription.customer = test_user_paid.stripe_customer_id
        mock_subscription.id = "sub_cancelled_123"

        handle_subscription_deleted(mock_subscription, db)

        db.refresh(test_user_paid)
        assert test_user_paid.subscription_tier == SubscriptionTier.EXPIRED
        assert test_user_paid.stripe_subscription_id is None

    def test_handle_invoice_payment_failed(self, db: Session, test_user_paid: User):
        """Test invoice.payment_failed webhook handler."""
        mock_invoice = MagicMock()
        mock_invoice.customer = test_user_paid.stripe_customer_id
        mock_invoice.id = "in_failed_123"

        # Should not raise, just log warning
        handle_invoice_payment_failed(mock_invoice, db)

        # User tier should not change immediately (Stripe will retry)
        db.refresh(test_user_paid)
        assert test_user_paid.subscription_tier == SubscriptionTier.STARTER_MONTHLY


class TestBillingAPI:
    """Tests for billing API endpoints."""

    def test_create_checkout_endpoint(self, client: TestClient, test_user: User, auth_headers: dict, mock_stripe):
        """Test POST /billing/create-checkout-session endpoint."""
        with patch("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_123"), \
             patch("app.core.config.settings.STRIPE_PRICE_STARTER_MONTHLY", "price_test"):
            response = client.post(
                "/api/v1/billing/create-checkout-session",
                headers=auth_headers,
                json={"tier_code": "STARTER_MONTHLY"}
            )

        assert response.status_code == 200
        assert "checkout_url" in response.json()

    def test_create_checkout_no_stripe_config(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test checkout fails without Stripe configuration."""
        with patch("app.core.config.settings.STRIPE_SECRET_KEY", ""):
            response = client.post(
                "/api/v1/billing/create-checkout-session",
                headers=auth_headers,
                json={"tier_code": "STARTER_MONTHLY"}
            )

        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]

    def test_create_portal_endpoint(self, client: TestClient, test_user_paid: User, auth_headers_paid: dict, mock_stripe):
        """Test POST /billing/create-portal-session endpoint."""
        with patch("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_123"):
            response = client.post(
                "/api/v1/billing/create-portal-session",
                headers=auth_headers_paid,
            )

        assert response.status_code == 200
        assert "portal_url" in response.json()

    def test_create_portal_no_customer(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test portal fails for user without customer ID."""
        with patch("app.core.config.settings.STRIPE_SECRET_KEY", "sk_test_123"):
            response = client.post(
                "/api/v1/billing/create-portal-session",
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "No active subscription" in response.json()["detail"]

    def test_webhook_endpoint(self, client: TestClient, db: Session, test_user: User):
        """Test POST /billing/webhook endpoint with valid signature."""
        import stripe
        import json

        # Create a mock event
        event_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_webhook",
                    "metadata": {
                        "user_id": str(test_user.id),
                        "tier_code": "STARTER_MONTHLY",
                    },
                    "subscription": "sub_webhook_test",
                }
            }
        }

        with patch("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test"), \
             patch("stripe.Webhook.construct_event") as mock_construct, \
             patch("stripe.Subscription.retrieve") as mock_sub:
            mock_construct.return_value = event_data
            mock_sub.return_value = MagicMock(
                current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp())
            )

            response = client.post(
                "/api/v1/billing/webhook",
                content=json.dumps(event_data),
                headers={"stripe-signature": "test_sig"}
            )

        assert response.status_code == 200

    def test_webhook_invalid_signature(self, client: TestClient):
        """Test webhook fails with invalid signature."""
        import stripe

        with patch("app.core.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test"), \
             patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "test_sig"
            )

            response = client.post(
                "/api/v1/billing/webhook",
                content="{}",
                headers={"stripe-signature": "invalid_sig"}
            )

        assert response.status_code == 400


class TestPriceMapping:
    """Tests for price ID mapping."""

    def test_price_map_keys(self):
        """Test that all expected tier codes are in the price map."""
        expected_tiers = [
            "STARTER_MONTHLY", "STARTER_ANNUALLY",
            "GROWTH_MONTHLY", "GROWTH_ANNUALLY",
            "PRO_MONTHLY", "PRO_ANNUALLY",
        ]
        for tier in expected_tiers:
            assert tier in PRICE_ID_MAP

    def test_tier_from_price_reverse_mapping(self):
        """Test reverse mapping from price ID to tier."""
        # Only non-empty price IDs should be mapped
        for price_id, tier in TIER_FROM_PRICE.items():
            if price_id:  # Skip empty price IDs
                assert tier in PRICE_ID_MAP
