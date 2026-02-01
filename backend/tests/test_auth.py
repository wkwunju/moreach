"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.tables import User, SubscriptionTier


class TestRegistration:
    """Tests for user registration."""

    def test_register_success(self, client: TestClient, db: Session, mock_sendgrid):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
                "company": "New Company",
                "job_title": "Engineer",
                "industry": "Technology",
                "usage_type": "Personal Use",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "message" in data

        # Verify user in database
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.email_verified is False
        assert user.subscription_tier == SubscriptionTier.FREE_TRIAL

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePassword123!",
                "full_name": "Duplicate User",
                "company": "Company",
                "job_title": "Engineer",
                "industry": "Technology",
                "usage_type": "Personal Use",
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "SecurePassword123!",
                "full_name": "Test User",
                "company": "Company",
                "job_title": "Engineer",
                "industry": "Technology",
                "usage_type": "Personal Use",
            }
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!",
            }
        )

        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_email(self, client: TestClient):
        """Test login with non-existent email fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            }
        )

        assert response.status_code == 401

    def test_login_unverified_email(self, client: TestClient, test_user_unverified: User):
        """Test login with unverified email fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_unverified.email,
                "password": "TestPassword123!",
            }
        )

        assert response.status_code == 403
        assert "verify your email" in response.json()["detail"]


class TestEmailVerification:
    """Tests for email verification."""

    def test_verify_email_valid_token(self, client: TestClient, test_user_unverified: User, db: Session):
        """Test email verification with valid token."""
        from app.core.auth import create_verification_token

        token = create_verification_token(test_user_unverified.email)

        response = client.post(
            f"/api/v1/auth/verify-email?token={token}"
        )

        assert response.status_code == 200

        # Refresh user from database
        db.refresh(test_user_unverified)
        assert test_user_unverified.email_verified is True

    def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification with invalid token fails."""
        response = client.post(
            "/api/v1/auth/verify-email?token=invalid_token"
        )

        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_resend_verification(self, client: TestClient, test_user_unverified: User, mock_sendgrid):
        """Test resending verification email."""
        response = client.post(
            f"/api/v1/auth/resend-verification?email={test_user_unverified.email}"
        )

        assert response.status_code == 200


class TestGetCurrentUser:
    """Tests for getting current user info."""

    def test_get_me_authenticated(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting current user with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["subscription_tier"] == "FREE_TRIAL"

    def test_get_me_no_token(self, client: TestClient):
        """Test getting current user without token fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # FastAPI returns 403 for missing credentials

    def test_get_me_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestGoogleAuth:
    """Tests for Google OAuth authentication."""

    @patch("httpx.get")
    def test_google_auth_new_user(self, mock_get, client: TestClient, db: Session, mock_sendgrid):
        """Test Google auth creates new user."""
        # Mock Google token validation
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "aud": "test_client_id",  # Must match settings
                "sub": "google_user_123",
                "email": "googleuser@gmail.com",
                "name": "Google User",
            }
        )

        with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "test_client_id"):
            response = client.post(
                "/api/v1/auth/google",
                json={"id_token": "test_google_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "googleuser@gmail.com"

    @patch("httpx.get")
    def test_google_auth_existing_user(self, mock_get, client: TestClient, test_user: User, db: Session):
        """Test Google auth links to existing user."""
        # Mock Google token validation
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "aud": "test_client_id",
                "sub": "google_user_456",
                "email": test_user.email,
                "name": "Test User",
            }
        )

        with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "test_client_id"):
            response = client.post(
                "/api/v1/auth/google",
                json={"id_token": "test_google_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == test_user.email

        # Check Google ID was linked
        db.refresh(test_user)
        assert test_user.google_id == "google_user_456"

    @patch("httpx.get")
    def test_google_auth_invalid_token(self, mock_get, client: TestClient):
        """Test Google auth with invalid token fails."""
        mock_get.return_value = MagicMock(status_code=400)

        with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "test_client_id"):
            response = client.post(
                "/api/v1/auth/google",
                json={"id_token": "invalid_token"}
            )

        assert response.status_code == 401


class TestCompleteProfile:
    """Tests for profile completion."""

    def test_complete_profile(self, client: TestClient, test_user: User, auth_headers: dict, db: Session):
        """Test completing user profile."""
        # First set profile_completed to False
        test_user.profile_completed = False
        db.commit()

        response = client.post(
            "/api/v1/auth/complete-profile",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "company": "Updated Company",
                "job_title": "Updated Title",
                "industry": "SaaS",
                "usage_type": "Agency Use",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["company"] == "Updated Company"
        assert data["profile_completed"] is True
