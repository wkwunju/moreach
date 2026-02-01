"""
Pytest fixtures for moreach backend tests.
"""

import pytest
from datetime import datetime, timedelta
from typing import Generator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.auth import get_password_hash, create_access_token
from app.models.tables import User, SubscriptionTier, UserRole, IndustryType, UsageType


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with the test database."""
    from app.main import app

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user with FREE_TRIAL subscription."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        company="Test Company",
        job_title="Developer",
        industry=IndustryType.TECH,
        usage_type=UsageType.PERSONAL,
        role=UserRole.USER,
        is_active=True,
        email_verified=True,
        profile_completed=True,
        subscription_tier=SubscriptionTier.FREE_TRIAL,
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_paid(db: Session) -> User:
    """Create a test user with STARTER_MONTHLY subscription."""
    user = User(
        email="paid@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Paid User",
        company="Paid Company",
        job_title="Manager",
        industry=IndustryType.TECH,
        usage_type=UsageType.PERSONAL,
        role=UserRole.USER,
        is_active=True,
        email_verified=True,
        profile_completed=True,
        subscription_tier=SubscriptionTier.STARTER_MONTHLY,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
        subscription_ends_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_expired(db: Session) -> User:
    """Create a test user with EXPIRED subscription."""
    user = User(
        email="expired@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Expired User",
        company="Expired Company",
        job_title="CEO",
        industry=IndustryType.TECH,
        usage_type=UsageType.PERSONAL,
        role=UserRole.USER,
        is_active=True,
        email_verified=True,
        profile_completed=True,
        subscription_tier=SubscriptionTier.EXPIRED,
        trial_ends_at=datetime.utcnow() - timedelta(days=7),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_unverified(db: Session) -> User:
    """Create a test user with unverified email."""
    user = User(
        email="unverified@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Unverified User",
        company="Test Company",
        job_title="Developer",
        industry=IndustryType.TECH,
        usage_type=UsageType.PERSONAL,
        role=UserRole.USER,
        is_active=True,
        email_verified=False,
        profile_completed=True,
        subscription_tier=SubscriptionTier.FREE_TRIAL,
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate auth headers for the test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_paid(test_user_paid: User) -> dict:
    """Generate auth headers for the paid test user."""
    token = create_access_token(data={"sub": str(test_user_paid.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_stripe():
    """Mock Stripe API for testing."""
    with patch("stripe.Customer.create") as mock_customer, \
         patch("stripe.checkout.Session.create") as mock_checkout, \
         patch("stripe.billing_portal.Session.create") as mock_portal, \
         patch("stripe.Subscription.retrieve") as mock_subscription:

        # Mock customer creation
        mock_customer.return_value = MagicMock(id="cus_test_new")

        # Mock checkout session
        mock_checkout.return_value = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test"
        )

        # Mock portal session
        mock_portal.return_value = MagicMock(
            url="https://billing.stripe.com/test"
        )

        # Mock subscription
        mock_subscription.return_value = MagicMock(
            id="sub_test_123",
            current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            status="active"
        )

        yield {
            "customer": mock_customer,
            "checkout": mock_checkout,
            "portal": mock_portal,
            "subscription": mock_subscription,
        }


@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid email for testing."""
    with patch("app.core.email.SendGridAPIClient") as mock_client:
        mock_instance = MagicMock()
        mock_instance.send.return_value = MagicMock(status_code=202)
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm():
    """Mock LLM calls for testing."""
    with patch("app.services.reddit.scoring.RedditScoringService.score_post") as mock_score:
        mock_score.return_value = {
            "relevancy_score": 85,
            "relevancy_reason": "Test reason",
            "suggested_comment": "Test comment",
            "suggested_dm": "Test DM",
        }
        yield mock_score
