"""Initial schema - create all tables

Revision ID: 0001
Revises:
Create Date: 2026-02-01

This migration creates all tables from scratch for a fresh PostgreSQL database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types first (PostgreSQL specific)
    user_role = sa.Enum('USER', 'ADMIN', name='userrole', create_type=False)
    industry_type = sa.Enum(
        'E-commerce', 'SaaS', 'Marketing Agency', 'Content Creator', 'Retail',
        'Fashion & Beauty', 'Health & Fitness', 'Food & Beverage', 'Technology',
        'Education', 'Other', name='industrytype', create_type=False
    )
    usage_type = sa.Enum('Personal Use', 'Agency Use', 'Team Use', name='usagetype', create_type=False)
    subscription_tier = sa.Enum(
        'FREE_TRIAL', 'MONTHLY', 'ANNUALLY', 'STARTER_MONTHLY', 'STARTER_ANNUALLY',
        'GROWTH_MONTHLY', 'GROWTH_ANNUALLY', 'PRO_MONTHLY', 'PRO_ANNUALLY', 'EXPIRED',
        name='subscriptiontier', create_type=False
    )
    request_status = sa.Enum('PARTIAL', 'PROCESSING', 'DONE', 'FAILED', name='requeststatus', create_type=False)
    campaign_status = sa.Enum('DISCOVERING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'DELETED', name='redditcampaignstatus', create_type=False)
    lead_status = sa.Enum('NEW', 'CONTACTED', 'DISMISSED', name='redditleadstatus', create_type=False)

    # Create enum types
    user_role.create(op.get_bind(), checkfirst=True)
    industry_type.create(op.get_bind(), checkfirst=True)
    usage_type.create(op.get_bind(), checkfirst=True)
    subscription_tier.create(op.get_bind(), checkfirst=True)
    request_status.create(op.get_bind(), checkfirst=True)
    campaign_status.create(op.get_bind(), checkfirst=True)
    lead_status.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(256), nullable=False),
        sa.Column('hashed_password', sa.String(256), nullable=True),
        sa.Column('google_id', sa.String(256), nullable=True),
        sa.Column('full_name', sa.String(256), server_default='', nullable=False),
        sa.Column('company', sa.String(256), server_default='', nullable=False),
        sa.Column('job_title', sa.String(256), server_default='', nullable=False),
        sa.Column('industry', sa.Enum('E-commerce', 'SaaS', 'Marketing Agency', 'Content Creator', 'Retail',
                                      'Fashion & Beauty', 'Health & Fitness', 'Food & Beverage', 'Technology',
                                      'Education', 'Other', name='industrytype'), server_default='Other', nullable=False),
        sa.Column('usage_type', sa.Enum('Personal Use', 'Agency Use', 'Team Use', name='usagetype'),
                  server_default='Personal Use', nullable=False),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), server_default='USER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('profile_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('subscription_tier', sa.Enum(
            'FREE_TRIAL', 'MONTHLY', 'ANNUALLY', 'STARTER_MONTHLY', 'STARTER_ANNUALLY',
            'GROWTH_MONTHLY', 'GROWTH_ANNUALLY', 'PRO_MONTHLY', 'PRO_ANNUALLY', 'EXPIRED',
            name='subscriptiontier'), server_default='FREE_TRIAL', nullable=False),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(256), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True)
    op.create_index('ix_users_stripe_subscription_id', 'users', ['stripe_subscription_id'], unique=False)

    # Requests table
    op.create_table('requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.Enum('PARTIAL', 'PROCESSING', 'DONE', 'FAILED', name='requeststatus'),
                  server_default='PARTIAL', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('constraints', sa.Text(), server_default='', nullable=False),
        sa.Column('intent', sa.Text(), server_default='', nullable=False),
        sa.Column('query_embedding', sa.Text(), server_default='', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Influencers table
    op.create_table('influencers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('handle', sa.String(128), nullable=False),
        sa.Column('name', sa.String(256), server_default='', nullable=False),
        sa.Column('bio', sa.Text(), server_default='', nullable=False),
        sa.Column('profile_summary', sa.Text(), server_default='', nullable=False),
        sa.Column('category', sa.String(128), server_default='', nullable=False),
        sa.Column('tags', sa.Text(), server_default='', nullable=False),
        sa.Column('followers', sa.Float(), server_default='0', nullable=False),
        sa.Column('avg_likes', sa.Float(), server_default='0', nullable=False),
        sa.Column('avg_comments', sa.Float(), server_default='0', nullable=False),
        sa.Column('avg_video_views', sa.Float(), server_default='0', nullable=False),
        sa.Column('highest_likes', sa.Float(), server_default='0', nullable=False),
        sa.Column('highest_comments', sa.Float(), server_default='0', nullable=False),
        sa.Column('highest_video_views', sa.Float(), server_default='0', nullable=False),
        sa.Column('post_sharing_percentage', sa.Float(), server_default='0', nullable=False),
        sa.Column('post_collaboration_percentage', sa.Float(), server_default='0', nullable=False),
        sa.Column('audience_analysis', sa.Text(), server_default='', nullable=False),
        sa.Column('collaboration_opportunity', sa.Text(), server_default='', nullable=False),
        sa.Column('email', sa.String(256), server_default='', nullable=False),
        sa.Column('external_url', sa.String(512), server_default='', nullable=False),
        sa.Column('external_id', sa.String(256), server_default='', nullable=False),
        sa.Column('platform', sa.String(64), server_default='instagram', nullable=False),
        sa.Column('country', sa.String(128), server_default='', nullable=False),
        sa.Column('gender', sa.String(64), server_default='', nullable=False),
        sa.Column('profile_url', sa.String(512), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_influencers_handle', 'influencers', ['handle'], unique=True)

    # Request Results table
    op.create_table('request_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), server_default='0', nullable=False),
        sa.Column('rank', sa.Integer(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id']),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'])
    )

    # Reddit Campaigns table
    op.create_table('reddit_campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.Enum('DISCOVERING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'DELETED',
                                    name='redditcampaignstatus'), server_default='DISCOVERING', nullable=False),
        sa.Column('business_description', sa.Text(), nullable=False),
        sa.Column('keywords', sa.Text(), server_default='', nullable=False),
        sa.Column('search_queries', sa.Text(), server_default='', nullable=False),
        sa.Column('poll_interval_hours', sa.Integer(), server_default='6', nullable=False),
        sa.Column('last_poll_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    op.create_index('ix_reddit_campaigns_user_id', 'reddit_campaigns', ['user_id'])

    # Reddit Campaign Subreddits table
    op.create_table('reddit_campaign_subreddits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('subreddit_name', sa.String(128), nullable=False),
        sa.Column('subreddit_title', sa.String(512), server_default='', nullable=False),
        sa.Column('subreddit_description', sa.Text(), server_default='', nullable=False),
        sa.Column('subscribers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['reddit_campaigns.id'])
    )

    # Reddit Leads table
    op.create_table('reddit_leads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('reddit_post_id', sa.String(128), nullable=False),
        sa.Column('subreddit_name', sa.String(128), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), server_default='', nullable=False),
        sa.Column('author', sa.String(128), nullable=False),
        sa.Column('post_url', sa.String(512), nullable=False),
        sa.Column('score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('num_comments', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_utc', sa.Float(), nullable=False),
        sa.Column('relevancy_score', sa.Float(), nullable=True),
        sa.Column('relevancy_reason', sa.Text(), server_default='', nullable=False),
        sa.Column('suggested_comment', sa.Text(), server_default='', nullable=False),
        sa.Column('suggested_dm', sa.Text(), server_default='', nullable=False),
        sa.Column('has_suggestions', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('suggestions_generated_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'CONTACTED', 'DISMISSED', name='redditleadstatus'),
                  server_default='NEW', nullable=False),
        sa.Column('discovered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['reddit_campaigns.id']),
        sa.UniqueConstraint('campaign_id', 'reddit_post_id', name='uq_campaign_post')
    )
    op.create_index('ix_reddit_leads_reddit_post_id', 'reddit_leads', ['reddit_post_id'])

    # Global Subreddit Polls table
    op.create_table('global_subreddit_polls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subreddit_name', sa.String(128), nullable=False),
        sa.Column('last_poll_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_post_timestamp', sa.Float(), server_default='0', nullable=False),
        sa.Column('poll_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_posts_found', sa.Integer(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_global_subreddit_polls_name', 'global_subreddit_polls', ['subreddit_name'], unique=True)

    # Subreddit Cache table
    op.create_table('subreddit_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('title', sa.String(512), server_default='', nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('subscribers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('url', sa.String(512), server_default='', nullable=False),
        sa.Column('is_nsfw', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reddit_created_utc', sa.Float(), nullable=True),
        sa.Column('discovered_via_queries', sa.Text(), server_default='[]', nullable=False),
        sa.Column('discovery_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('first_discovered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('embedding_status', sa.String(32), server_default='pending', nullable=False),
        sa.Column('embedding_updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subreddit_cache_name', 'subreddit_cache', ['name'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('subreddit_cache')
    op.drop_table('global_subreddit_polls')
    op.drop_table('reddit_leads')
    op.drop_table('reddit_campaign_subreddits')
    op.drop_table('reddit_campaigns')
    op.drop_table('request_results')
    op.drop_table('influencers')
    op.drop_table('requests')
    op.drop_table('users')

    # Drop enum types
    sa.Enum(name='redditleadstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='redditcampaignstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='requeststatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscriptiontier').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='usagetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='industrytype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
