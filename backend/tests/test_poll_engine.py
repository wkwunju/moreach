"""
Tests for unified PollEngine and PollJob model.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session

from app.models.tables import (
    User, RedditCampaign, RedditCampaignSubreddit, RedditLead,
    RedditCampaignStatus, RedditLeadStatus,
    PollJob, PollJobStatus,
    SubscriptionTier,
)
from app.services.reddit.poll_engine import PollEngine, PollEngineCallbacks, run_poll_sync


class TestPollJobModel:
    """Tests for the PollJob model."""

    def test_create_poll_job(self, db: Session, test_campaign: RedditCampaign):
        """Test creating a PollJob record."""
        job = PollJob(
            campaign_id=test_campaign.id,
            status=PollJobStatus.RUNNING,
            trigger="manual",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        assert job.id is not None
        assert job.campaign_id == test_campaign.id
        assert job.status == PollJobStatus.RUNNING
        assert job.trigger == "manual"
        assert job.posts_fetched == 0
        assert job.leads_created == 0
        assert job.started_at is not None
        assert job.completed_at is None

    def test_poll_job_campaign_relationship(self, db: Session, test_campaign: RedditCampaign):
        """Test PollJob -> Campaign relationship."""
        job = PollJob(
            campaign_id=test_campaign.id,
            status=PollJobStatus.COMPLETED,
            trigger="scheduled",
            posts_fetched=50,
            leads_created=10,
            completed_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        assert job.campaign.id == test_campaign.id
        assert job.campaign.business_description == test_campaign.business_description

    def test_campaign_poll_jobs_relationship(self, db: Session, test_campaign: RedditCampaign):
        """Test Campaign -> PollJobs relationship."""
        job1 = PollJob(campaign_id=test_campaign.id, status=PollJobStatus.COMPLETED, trigger="manual")
        job2 = PollJob(campaign_id=test_campaign.id, status=PollJobStatus.COMPLETED, trigger="scheduled")
        db.add_all([job1, job2])
        db.commit()
        db.refresh(test_campaign)

        assert len(test_campaign.poll_jobs) == 2

    def test_lead_poll_job_relationship(self, db: Session, test_campaign: RedditCampaign):
        """Test RedditLead -> PollJob relationship."""
        job = PollJob(campaign_id=test_campaign.id, status=PollJobStatus.RUNNING, trigger="manual")
        db.add(job)
        db.commit()
        db.refresh(job)

        lead = RedditLead(
            campaign_id=test_campaign.id,
            poll_job_id=job.id,
            reddit_post_id="test123",
            subreddit_name="test",
            title="Test Post",
            content="Test content",
            author="test_author",
            post_url="https://reddit.com/test",
            score=10,
            num_comments=2,
            created_utc=datetime.utcnow().timestamp(),
            relevancy_score=85,
            relevancy_reason="Test",
            status=RedditLeadStatus.NEW,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        assert lead.poll_job_id == job.id
        assert lead.poll_job.id == job.id

    def test_lead_without_poll_job(self, db: Session, test_campaign: RedditCampaign):
        """Test that leads without poll_job_id still work (backward compat)."""
        lead = RedditLead(
            campaign_id=test_campaign.id,
            poll_job_id=None,
            reddit_post_id="old_lead",
            subreddit_name="test",
            title="Old Lead",
            content="Before PollJob was added",
            author="author",
            post_url="https://reddit.com/old",
            score=5,
            num_comments=1,
            created_utc=datetime.utcnow().timestamp(),
            relevancy_score=70,
            relevancy_reason="Old lead",
            status=RedditLeadStatus.NEW,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        assert lead.poll_job_id is None
        assert lead.poll_job is None

    def test_poll_job_leads_relationship(self, db: Session, test_campaign: RedditCampaign):
        """Test PollJob -> Leads relationship."""
        job = PollJob(campaign_id=test_campaign.id, status=PollJobStatus.RUNNING, trigger="manual")
        db.add(job)
        db.commit()
        db.refresh(job)

        for i in range(3):
            lead = RedditLead(
                campaign_id=test_campaign.id,
                poll_job_id=job.id,
                reddit_post_id=f"post_{i}",
                subreddit_name="test",
                title=f"Post {i}",
                content="Content",
                author="author",
                post_url=f"https://reddit.com/post_{i}",
                score=10,
                num_comments=1,
                created_utc=datetime.utcnow().timestamp(),
                status=RedditLeadStatus.NEW,
            )
            db.add(lead)
        db.commit()
        db.refresh(job)

        assert len(job.leads) == 3

    def test_poll_job_status_enum(self):
        """Test PollJobStatus enum values."""
        assert PollJobStatus.RUNNING.value == "RUNNING"
        assert PollJobStatus.COMPLETED.value == "COMPLETED"
        assert PollJobStatus.FAILED.value == "FAILED"
        assert PollJobStatus.PARTIAL.value == "PARTIAL"


class TestPollEngine:
    """Tests for the PollEngine."""

    def test_poll_engine_invalid_campaign(self, db: Session):
        """Test PollEngine with non-existent campaign."""
        engine = PollEngine()
        with pytest.raises(ValueError, match="not found"):
            asyncio.run(engine.run_poll(db, campaign_id=99999))

    def test_poll_engine_inactive_campaign(self, db: Session, test_campaign: RedditCampaign):
        """Test PollEngine with paused campaign."""
        test_campaign.status = RedditCampaignStatus.PAUSED
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="not active"):
            asyncio.run(engine.run_poll(db, test_campaign.id))

    def test_poll_engine_no_subreddits(self, db: Session, test_campaign: RedditCampaign):
        """Test PollEngine with campaign that has no active subreddits."""
        engine = PollEngine()
        with pytest.raises(ValueError, match="No active subreddits"):
            asyncio.run(engine.run_poll(db, test_campaign.id))

    @patch("app.services.reddit.poll_engine.get_reddit_provider")
    @patch("app.services.reddit.poll_engine.BatchScoringService")
    @patch("app.services.reddit.poll_engine.send_poll_summary_email")
    def test_poll_engine_no_new_posts(
        self, mock_email, mock_scoring_cls, mock_provider_fn,
        db: Session, test_campaign_with_subreddits: RedditCampaign
    ):
        """Test PollEngine when subreddits return no new posts."""
        mock_provider = MagicMock()
        mock_provider.scrape_subreddit.return_value = []
        mock_provider_fn.return_value = mock_provider

        engine = PollEngine()
        engine.reddit_provider = mock_provider

        poll_job = asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

        assert poll_job.status == PollJobStatus.COMPLETED
        assert poll_job.posts_fetched == 0
        assert poll_job.leads_created == 0

    @patch("app.services.reddit.poll_engine.get_reddit_provider")
    @patch("app.services.reddit.poll_engine.send_poll_summary_email")
    @patch("app.services.reddit.poll_engine.track_api_call")
    def test_poll_engine_full_pipeline(
        self, mock_track, mock_email, mock_provider_fn,
        db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine full pipeline: fetch → save → score → cleanup → suggestions → email."""
        # Mock Reddit provider
        mock_provider = MagicMock()
        mock_provider.scrape_subreddit.return_value = [
            {
                "id": "post_high",
                "title": "Need code review tool",
                "content": "Looking for good code review tools",
                "author": "dev_user",
                "url": "https://reddit.com/r/programming/post_high",
                "score": 50,
                "num_comments": 10,
                "created_utc": datetime.utcnow().timestamp(),
                "subreddit_name": "programming",
            },
            {
                "id": "post_low",
                "title": "Random meme",
                "content": "Just a meme, not relevant",
                "author": "meme_user",
                "url": "https://reddit.com/r/programming/post_low",
                "score": 100,
                "num_comments": 50,
                "created_utc": datetime.utcnow().timestamp(),
                "subreddit_name": "programming",
            },
        ]
        mock_provider_fn.return_value = mock_provider

        # Mock batch scoring service
        mock_scoring = MagicMock()
        # batch_quick_score returns scored posts
        async def mock_batch_score(posts, desc, **kwargs):
            results = []
            for p in posts:
                if p["id"] == "post_high":
                    results.append({**p, "relevancy_score": 90, "relevancy_reason": "Highly relevant", "has_suggestions": False})
                else:
                    results.append({**p, "relevancy_score": 30, "relevancy_reason": "Not relevant", "has_suggestions": False})
            return results
        mock_scoring.batch_quick_score = mock_batch_score
        mock_scoring.get_llm_calls_made.return_value = 1

        # suggestions for high score
        async def mock_suggestions(posts, desc, **kwargs):
            for p in posts:
                if p.get("relevancy_score", 0) >= 90:
                    p["suggested_comment"] = "Great question!"
                    p["suggested_dm"] = "Hi there!"
                    p["has_suggestions"] = True
            return posts
        mock_scoring.generate_suggestions_for_high_score = mock_suggestions

        engine = PollEngine()
        engine.reddit_provider = mock_provider
        engine.scoring_service = mock_scoring

        poll_job = asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id, trigger="manual"))

        # Verify PollJob
        assert poll_job.status == PollJobStatus.COMPLETED
        assert poll_job.trigger == "manual"
        assert poll_job.completed_at is not None
        # 2 subreddits, each returns 2 posts, but dedup means second sub's posts are duplicates
        # So posts_fetched >= 2
        assert poll_job.posts_fetched >= 2

        # post_low (score 30) should be deleted, post_high (score 90) should be kept
        assert poll_job.leads_created >= 1
        assert poll_job.leads_deleted >= 1

        # Verify the surviving lead
        surviving_leads = db.query(RedditLead).filter(
            RedditLead.poll_job_id == poll_job.id
        ).all()

        assert len(surviving_leads) >= 1
        high_lead = next((l for l in surviving_leads if l.reddit_post_id == "post_high"), None)
        assert high_lead is not None
        assert high_lead.relevancy_score == 90
        assert high_lead.poll_job_id == poll_job.id

        # post_low should NOT exist (deleted due to score < 50)
        low_lead = next((l for l in surviving_leads if l.reddit_post_id == "post_low"), None)
        assert low_lead is None

    @patch("app.services.reddit.poll_engine.get_reddit_provider")
    @patch("app.services.reddit.poll_engine.send_poll_summary_email")
    @patch("app.services.reddit.poll_engine.track_api_call")
    def test_poll_engine_callbacks(
        self, mock_track, mock_email, mock_provider_fn,
        db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test that PollEngine calls callbacks correctly."""
        mock_provider = MagicMock()
        mock_provider.scrape_subreddit.return_value = [
            {
                "id": "cb_post",
                "title": "Callback test post",
                "content": "Test",
                "author": "test",
                "url": "https://reddit.com/test",
                "score": 10,
                "num_comments": 1,
                "created_utc": datetime.utcnow().timestamp(),
                "subreddit_name": "programming",
            }
        ]
        mock_provider_fn.return_value = mock_provider

        mock_scoring = MagicMock()
        async def mock_score(posts, desc, **kwargs):
            return [{**p, "relevancy_score": 80, "relevancy_reason": "Good", "has_suggestions": False} for p in posts]
        mock_scoring.batch_quick_score = mock_score
        mock_scoring.get_llm_calls_made.return_value = 1
        async def mock_sugg(posts, desc, **kwargs):
            return posts
        mock_scoring.generate_suggestions_for_high_score = mock_sugg

        # Track callback invocations
        progress_calls = []
        lead_calls = []
        complete_calls = []

        class TrackingCallbacks(PollEngineCallbacks):
            async def on_progress(self, phase, current, total, message, **extra):
                progress_calls.append({"phase": phase, "current": current, "total": total})

            async def on_lead_created(self, lead):
                lead_calls.append(lead.id)

            async def on_complete(self, stats):
                complete_calls.append(stats)

        engine = PollEngine()
        engine.reddit_provider = mock_provider
        engine.scoring_service = mock_scoring

        callbacks = TrackingCallbacks()
        poll_job = asyncio.run(engine.run_poll(
            db, test_campaign_with_subreddits.id, callbacks=callbacks
        ))

        # Should have progress events for fetching and scoring phases
        phases = [c["phase"] for c in progress_calls]
        assert "fetching" in phases
        assert "scoring" in phases

        # Should have lead events for surviving leads
        assert len(lead_calls) >= 1

        # Should have exactly one complete event
        assert len(complete_calls) == 1
        assert "total_leads" in complete_calls[0]

    def test_poll_engine_trigger_types(self, db: Session, test_campaign_with_subreddits: RedditCampaign):
        """Test different trigger types create PollJob with correct trigger."""
        # We just test that PollJob creation works with trigger param
        job1 = PollJob(campaign_id=test_campaign_with_subreddits.id, status=PollJobStatus.RUNNING, trigger="manual")
        job2 = PollJob(campaign_id=test_campaign_with_subreddits.id, status=PollJobStatus.RUNNING, trigger="scheduled")
        job3 = PollJob(campaign_id=test_campaign_with_subreddits.id, status=PollJobStatus.RUNNING, trigger="first_poll")
        db.add_all([job1, job2, job3])
        db.commit()

        assert job1.trigger == "manual"
        assert job2.trigger == "scheduled"
        assert job3.trigger == "first_poll"


class TestPollEngineUserValidation:
    """Tests for PollEngine user and campaign status validation."""

    def test_poll_engine_rejects_deactivated_user(
        self, db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine rejects poll when user is_active=False."""
        test_user.is_active = False
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="deactivated"):
            asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

    def test_poll_engine_rejects_blocked_user(
        self, db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine rejects poll when user is_blocked=True."""
        test_user.is_blocked = True
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="blocked"):
            asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

    def test_poll_engine_rejects_expired_subscription(
        self, db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine rejects poll when subscription_tier=EXPIRED."""
        test_user.subscription_tier = SubscriptionTier.EXPIRED
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="expired"):
            asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

    def test_poll_engine_rejects_expired_trial(
        self, db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine rejects poll when free trial has ended by date."""
        test_user.subscription_tier = SubscriptionTier.FREE_TRIAL
        test_user.trial_ends_at = datetime.utcnow() - timedelta(days=1)
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="free trial has ended"):
            asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

    def test_poll_engine_rejects_expired_paid_subscription(
        self, db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine rejects poll when paid subscription has ended by date."""
        test_user.subscription_tier = SubscriptionTier.STARTER_MONTHLY
        test_user.subscription_ends_at = datetime.utcnow() - timedelta(days=1)
        db.commit()

        engine = PollEngine()
        with pytest.raises(ValueError, match="subscription has ended"):
            asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))

    @patch("app.services.reddit.poll_engine.get_reddit_provider")
    @patch("app.services.reddit.poll_engine.BatchScoringService")
    @patch("app.services.reddit.poll_engine.send_poll_summary_email")
    def test_poll_engine_allows_active_user(
        self, mock_email, mock_scoring_cls, mock_provider_fn,
        db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine allows poll for active user with valid subscription."""
        mock_provider = MagicMock()
        mock_provider.scrape_subreddit.return_value = []
        mock_provider_fn.return_value = mock_provider

        engine = PollEngine()
        engine.reddit_provider = mock_provider

        # Should not raise - user is active with valid FREE_TRIAL
        poll_job = asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))
        assert poll_job.status == PollJobStatus.COMPLETED

    @patch("app.services.reddit.poll_engine.get_reddit_provider")
    @patch("app.services.reddit.poll_engine.BatchScoringService")
    @patch("app.services.reddit.poll_engine.send_poll_summary_email")
    def test_poll_engine_allows_trial_not_yet_expired(
        self, mock_email, mock_scoring_cls, mock_provider_fn,
        db: Session, test_campaign_with_subreddits: RedditCampaign, test_user: User
    ):
        """Test PollEngine allows poll when trial hasn't expired yet."""
        test_user.subscription_tier = SubscriptionTier.FREE_TRIAL
        test_user.trial_ends_at = datetime.utcnow() + timedelta(days=3)
        db.commit()

        mock_provider = MagicMock()
        mock_provider.scrape_subreddit.return_value = []
        mock_provider_fn.return_value = mock_provider

        engine = PollEngine()
        engine.reddit_provider = mock_provider

        poll_job = asyncio.run(engine.run_poll(db, test_campaign_with_subreddits.id))
        assert poll_job.status == PollJobStatus.COMPLETED


class TestSchedulerIntegration:
    """Tests for scheduler using the new PollEngine."""

    def test_scheduler_passes_trigger(self, db: Session, test_campaign_with_subreddits: RedditCampaign):
        """Test that scheduler passes trigger='scheduled' through polling service."""
        from app.services.reddit.polling import RedditPollingService

        with patch("app.services.reddit.poll_engine.run_poll_sync") as mock_run:
            mock_job = MagicMock()
            mock_job.id = 1
            mock_job.subreddits_polled = 2
            mock_job.posts_fetched = 10
            mock_job.leads_created = 5
            mock_run.return_value = mock_job

            service = RedditPollingService()
            result = service.poll_campaign_immediately(
                db, test_campaign_with_subreddits.id, trigger="scheduled"
            )

            mock_run.assert_called_once_with(
                db, test_campaign_with_subreddits.id, trigger="scheduled"
            )
            assert result["poll_job_id"] == 1
            assert result["total_leads_created"] == 5


class TestStreamingPollIntegration:
    """Tests for streaming poll using PollEngine."""

    def test_streaming_service_imports(self):
        """Test that StreamingPollService can be imported and initialized."""
        from app.services.reddit.streaming_poll import StreamingPollService
        # StreamingPollService.__init__ creates a PollEngine, which creates
        # reddit_provider and scoring_service. We just verify the class exists.
        assert StreamingPollService is not None

    def test_sync_wrapper_imports(self):
        """Test that poll_campaign_with_batch_scoring can be imported."""
        from app.services.reddit.streaming_poll import poll_campaign_with_batch_scoring
        assert poll_campaign_with_batch_scoring is not None


# Reuse existing fixtures from conftest.py
@pytest.fixture
def test_campaign(db: Session, test_user: User) -> RedditCampaign:
    """Create a test campaign."""
    import json
    campaign = RedditCampaign(
        user_id=test_user.id,
        business_description="AI-powered code review tool for developers",
        search_queries=json.dumps(["code review", "developer tools"]),
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
