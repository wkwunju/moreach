"""
Tests for Reddit campaign functionality.
"""

import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.tables import (
    User, RedditCampaign, RedditCampaignSubreddit, RedditLead,
    RedditCampaignStatus, RedditLeadStatus
)


@pytest.fixture
def test_campaign(db: Session, test_user: User) -> RedditCampaign:
    """Create a test campaign."""
    campaign = RedditCampaign(
        user_id=test_user.id,
        business_description="AI-powered code review tool for developers",
        search_queries=json.dumps(["code review", "developer tools", "CI/CD"]),
        poll_interval_hours=6,
        status=RedditCampaignStatus.ACTIVE,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@pytest.fixture
def test_campaign_with_subreddits(db: Session, test_campaign: RedditCampaign) -> RedditCampaign:
    """Create a test campaign with subreddits."""
    subreddits = [
        RedditCampaignSubreddit(
            campaign_id=test_campaign.id,
            subreddit_name="programming",
            subreddit_title="r/programming",
            subreddit_description="Computer Programming",
            subscribers=5000000,
            relevance_score=0.9,
            is_active=True,
        ),
        RedditCampaignSubreddit(
            campaign_id=test_campaign.id,
            subreddit_name="webdev",
            subreddit_title="r/webdev",
            subreddit_description="Web Development",
            subscribers=2000000,
            relevance_score=0.85,
            is_active=True,
        ),
    ]
    for sub in subreddits:
        db.add(sub)
    db.commit()
    db.refresh(test_campaign)
    return test_campaign


@pytest.fixture
def test_leads(db: Session, test_campaign: RedditCampaign) -> list:
    """Create test leads for a campaign."""
    leads = [
        RedditLead(
            campaign_id=test_campaign.id,
            reddit_post_id="abc123",
            subreddit_name="programming",
            title="Looking for code review tools",
            content="What are the best code review tools for a small team?",
            author="test_author",
            post_url="https://reddit.com/r/programming/comments/abc123",
            score=50,
            num_comments=10,
            created_utc=datetime.utcnow().timestamp(),
            relevancy_score=85,
            relevancy_reason="Highly relevant post about code review",
            suggested_comment="Great question! Consider trying...",
            suggested_dm="Hi! I noticed your interest in...",
            status=RedditLeadStatus.NEW,
        ),
        RedditLead(
            campaign_id=test_campaign.id,
            reddit_post_id="def456",
            subreddit_name="webdev",
            title="Best CI/CD tools for web apps",
            content="Need recommendations for CI/CD pipeline setup",
            author="another_author",
            post_url="https://reddit.com/r/webdev/comments/def456",
            score=30,
            num_comments=5,
            created_utc=datetime.utcnow().timestamp(),
            relevancy_score=75,
            relevancy_reason="Relevant discussion about development tools",
            suggested_comment="I'd recommend looking into...",
            suggested_dm="Hey! Saw your post about CI/CD...",
            status=RedditLeadStatus.NEW,
        ),
    ]
    for lead in leads:
        db.add(lead)
    db.commit()
    return leads


class TestCampaignCreation:
    """Tests for campaign creation."""

    def test_create_campaign(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test creating a new campaign."""
        with patch("app.services.reddit.discovery.RedditDiscoveryService.generate_search_queries") as mock_queries:
            mock_queries.return_value = ["code review", "developer tools"]

            response = client.post(
                "/api/v1/reddit/campaigns",
                headers=auth_headers,
                json={
                    "business_description": "AI-powered code review tool",
                    "poll_interval_hours": 6,
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DISCOVERING"
        assert "id" in data

    def test_create_campaign_unauthenticated(self, client: TestClient):
        """Test creating campaign without auth fails."""
        response = client.post(
            "/api/v1/reddit/campaigns",
            json={
                "business_description": "Test product",
                "poll_interval_hours": 6,
            }
        )

        assert response.status_code == 403  # FastAPI returns 403 for missing credentials


class TestSubredditDiscovery:
    """Tests for subreddit discovery."""

    def test_discover_subreddits(self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict):
        """Test discovering subreddits for a campaign."""
        with patch("app.services.reddit.discovery.RedditDiscoveryService.discover_subreddits") as mock_discover, \
             patch("app.services.reddit.discovery.RedditDiscoveryService.rank_subreddits") as mock_rank:
            mock_discover.return_value = [
                {
                    "name": "programming",
                    "title": "r/programming",
                    "description": "Computer Programming",
                    "subscribers": 5000000,
                    "url": "https://reddit.com/r/programming",
                }
            ]
            mock_rank.return_value = [
                {
                    "name": "programming",
                    "title": "r/programming",
                    "description": "Computer Programming",
                    "subscribers": 5000000,
                    "url": "https://reddit.com/r/programming",
                    "relevance_score": 0.9,
                }
            ]

            response = client.get(
                f"/api/v1/reddit/campaigns/{test_campaign.id}/discover-subreddits",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "programming"

    def test_discover_subreddits_other_user(
        self, client: TestClient, test_campaign: RedditCampaign, test_user_paid: User, auth_headers_paid: dict
    ):
        """Test discovering subreddits for another user's campaign fails."""
        response = client.get(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/discover-subreddits",
            headers=auth_headers_paid,
        )

        assert response.status_code == 403


class TestSubredditSelection:
    """Tests for subreddit selection."""

    def test_select_subreddits(self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session):
        """Test selecting subreddits for a campaign."""
        response = client.post(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/select-subreddits",
            headers=auth_headers,
            json={
                "subreddits": [
                    {
                        "name": "programming",
                        "title": "r/programming",
                        "description": "Computer Programming",
                        "subscribers": 5000000,
                        "relevance_score": 0.9,
                    },
                    {
                        "name": "webdev",
                        "title": "r/webdev",
                        "description": "Web Development",
                        "subscribers": 2000000,
                        "relevance_score": 0.85,
                    },
                ]
            }
        )

        assert response.status_code == 200
        assert "2 subreddits" in response.json()["message"]

        # Verify campaign is now ACTIVE
        db.refresh(test_campaign)
        assert test_campaign.status == RedditCampaignStatus.ACTIVE

    def test_select_subreddits_backward_compat(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict
    ):
        """Test selecting subreddits with old format (names only)."""
        response = client.post(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/select-subreddits",
            headers=auth_headers,
            json={
                "subreddit_names": ["programming", "webdev"]
            }
        )

        assert response.status_code == 200


class TestCampaignLeads:
    """Tests for campaign leads."""

    def test_get_leads(
        self, client: TestClient, test_campaign: RedditCampaign, test_leads: list, auth_headers: dict
    ):
        """Test getting leads for a campaign."""
        response = client.get(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/leads",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 2
        assert len(data["leads"]) == 2

    def test_get_leads_filtered_by_status(
        self, client: TestClient, test_campaign: RedditCampaign, test_leads: list, auth_headers: dict
    ):
        """Test filtering leads by status."""
        response = client.get(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/leads?status=NEW",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(lead["status"] == "NEW" for lead in data["leads"])

    def test_get_leads_sorted_by_relevancy(
        self, client: TestClient, test_campaign: RedditCampaign, test_leads: list, auth_headers: dict
    ):
        """Test leads are sorted by relevancy score."""
        response = client.get(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/leads",
            headers=auth_headers,
        )

        data = response.json()
        scores = [lead["relevancy_score"] for lead in data["leads"]]
        assert scores == sorted(scores, reverse=True)


class TestLeadManagement:
    """Tests for lead status management."""

    def test_update_lead_status(
        self, client: TestClient, test_leads: list, auth_headers: dict, db: Session
    ):
        """Test updating lead status."""
        lead = test_leads[0]
        response = client.patch(
            f"/api/v1/reddit/leads/{lead.id}/status",
            headers=auth_headers,
            json={"status": "CONTACTED"}
        )

        assert response.status_code == 200

        db.refresh(lead)
        assert lead.status == RedditLeadStatus.CONTACTED

    def test_update_lead_invalid_status(
        self, client: TestClient, test_leads: list, auth_headers: dict
    ):
        """Test updating lead with invalid status fails."""
        lead = test_leads[0]
        response = client.patch(
            f"/api/v1/reddit/leads/{lead.id}/status",
            headers=auth_headers,
            json={"status": "INVALID_STATUS"}
        )

        assert response.status_code == 400


class TestCampaignManagement:
    """Tests for campaign management."""

    def test_pause_campaign(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session
    ):
        """Test pausing a campaign."""
        response = client.post(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/pause",
            headers=auth_headers,
        )

        assert response.status_code == 200

        db.refresh(test_campaign)
        assert test_campaign.status == RedditCampaignStatus.PAUSED

    def test_resume_campaign(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session
    ):
        """Test resuming a campaign."""
        # First pause it
        test_campaign.status = RedditCampaignStatus.PAUSED
        db.commit()

        response = client.post(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/resume",
            headers=auth_headers,
        )

        assert response.status_code == 200

        db.refresh(test_campaign)
        assert test_campaign.status == RedditCampaignStatus.ACTIVE

    def test_delete_campaign(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session
    ):
        """Test deleting a campaign (soft delete)."""
        response = client.delete(
            f"/api/v1/reddit/campaigns/{test_campaign.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        db.refresh(test_campaign)
        assert test_campaign.status == RedditCampaignStatus.DELETED

    def test_list_campaigns_excludes_deleted(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session
    ):
        """Test that deleted campaigns are not listed."""
        # Delete the campaign
        test_campaign.status = RedditCampaignStatus.DELETED
        db.commit()

        response = client.get(
            "/api/v1/reddit/campaigns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestRunCampaign:
    """Tests for running campaigns manually."""

    def test_run_campaign_now(
        self, client: TestClient, test_campaign_with_subreddits: RedditCampaign, auth_headers: dict
    ):
        """Test running a campaign immediately."""
        with patch("app.services.reddit.polling.RedditPollingService.poll_campaign_immediately") as mock_poll:
            mock_poll.return_value = {
                "posts_fetched": 10,
                "leads_added": 5,
                "leads_updated": 2,
            }

            response = client.post(
                f"/api/v1/reddit/campaigns/{test_campaign_with_subreddits.id}/run-now",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_run_paused_campaign_fails(
        self, client: TestClient, test_campaign: RedditCampaign, auth_headers: dict, db: Session
    ):
        """Test running a paused campaign fails."""
        test_campaign.status = RedditCampaignStatus.PAUSED
        db.commit()

        response = client.post(
            f"/api/v1/reddit/campaigns/{test_campaign.id}/run-now",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "must be ACTIVE" in response.json()["detail"]


class TestGenerateSuggestions:
    """Tests for on-demand suggestion generation."""

    def test_generate_suggestions_for_lead(
        self, client: TestClient, test_campaign: RedditCampaign, db: Session, auth_headers: dict
    ):
        """Test generating suggestions for a lead without them."""
        # Create lead without suggestions
        lead = RedditLead(
            campaign_id=test_campaign.id,
            reddit_post_id="nosuggest123",
            subreddit_name="programming",
            title="Need help with testing",
            content="What testing frameworks do you recommend?",
            author="test_user",
            post_url="https://reddit.com/r/programming/comments/nosuggest123",
            score=20,
            num_comments=3,
            created_utc=datetime.utcnow().timestamp(),
            relevancy_score=70,
            relevancy_reason="Testing discussion",
            suggested_comment=None,
            suggested_dm=None,
            has_suggestions=False,
            status=RedditLeadStatus.NEW,
        )
        db.add(lead)
        db.commit()

        with patch("app.services.reddit.batch_scoring.BatchScoringService.generate_suggestion_on_demand") as mock_gen:
            mock_gen.return_value = {
                "suggested_comment": "Generated comment",
                "suggested_dm": "Generated DM",
            }

            response = client.post(
                f"/api/v1/reddit/leads/{lead.id}/generate-suggestions",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["suggested_comment"] == "Generated comment"
        assert data["cached"] is False

    def test_return_cached_suggestions(
        self, client: TestClient, test_leads: list, auth_headers: dict
    ):
        """Test returning existing suggestions without regenerating."""
        lead = test_leads[0]
        lead.has_suggestions = True

        response = client.post(
            f"/api/v1/reddit/leads/{lead.id}/generate-suggestions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
