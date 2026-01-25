"""
Reddit Polling Service
Implements CENTRALIZED DEDUPLICATED POLLING using Apify:
- Even if 100 users follow r/SaaS, we only poll it ONCE per cycle
- Then distribute relevant leads to each user's campaign
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import (
    RedditCampaign, 
    RedditCampaignSubreddit, 
    RedditLead,
    RedditLeadStatus,
    GlobalSubredditPoll,
    RedditCampaignStatus
)
from app.providers.reddit.apify import ApifyRedditProvider
from app.services.reddit.scoring import RedditScoringService


logger = logging.getLogger(__name__)


class RedditPollingService:
    """
    Centralized Reddit polling service using Apify Reddit Scraper actor
    """
    
    def __init__(self):
        self.reddit_provider = ApifyRedditProvider()
        self.scoring_service = RedditScoringService()
    
    def get_subreddits_to_poll(self, db: Session, max_age_hours: int = 6) -> List[str]:
        """
        Get list of subreddits that need polling
        
        Strategy:
        1. Find all active campaigns
        2. Collect all their subreddits
        3. Deduplicate
        4. Filter out recently polled ones
        """
        # Get all active campaigns
        active_campaigns = db.execute(
            select(RedditCampaign).where(
                RedditCampaign.status == RedditCampaignStatus.ACTIVE
            )
        ).scalars().all()
        
        if not active_campaigns:
            logger.info("No active campaigns found")
            return []
        
        # Collect all active subreddits across all campaigns
        all_subreddits = set()
        for campaign in active_campaigns:
            for sub in campaign.subreddits:
                if sub.is_active:
                    all_subreddits.add(sub.subreddit_name)
        
        logger.info(f"Found {len(all_subreddits)} unique subreddits across {len(active_campaigns)} campaigns")
        
        # Filter out recently polled subreddits
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        subreddits_to_poll = []
        
        for subreddit_name in all_subreddits:
            # Check last poll time
            poll_record = db.execute(
                select(GlobalSubredditPoll).where(
                    GlobalSubredditPoll.subreddit_name == subreddit_name
                )
            ).scalar_one_or_none()
            
            if poll_record is None:
                # Never polled before
                subreddits_to_poll.append(subreddit_name)
            elif poll_record.last_poll_at < cutoff_time:
                # Poll is stale
                subreddits_to_poll.append(subreddit_name)
            else:
                logger.debug(f"Skipping r/{subreddit_name} - recently polled")
        
        logger.info(f"{len(subreddits_to_poll)} subreddits need polling")
        return subreddits_to_poll
    
    def poll_subreddit(
        self, 
        db: Session, 
        subreddit_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Poll a single subreddit for new posts using Apify Reddit Scraper
        Updates GlobalSubredditPoll tracking
        """
        logger.info(f"Polling r/{subreddit_name}")
        
        # Get last poll info
        poll_record = db.execute(
            select(GlobalSubredditPoll).where(
                GlobalSubredditPoll.subreddit_name == subreddit_name
            )
        ).scalar_one_or_none()
        
        # Determine time filter based on last poll
        time_filter = "day"  # Default: last 24 hours
        since_timestamp = None
        
        if poll_record and poll_record.last_poll_at:
            hours_since_last_poll = (datetime.utcnow() - poll_record.last_poll_at).total_seconds() / 3600
            
            # Choose appropriate Reddit time filter based on interval
            if hours_since_last_poll <= 1:
                time_filter = "hour"
            elif hours_since_last_poll <= 24:
                time_filter = "day"
            elif hours_since_last_poll <= 168:  # 7 days
                time_filter = "week"
            elif hours_since_last_poll <= 720:  # 30 days
                time_filter = "month"
            else:
                time_filter = "year"
            
            since_timestamp = poll_record.last_post_timestamp
            logger.info(f"Last polled {hours_since_last_poll:.1f}h ago, using time_filter='{time_filter}'")
        else:
            # First poll: look back 24 hours
            since_timestamp = (datetime.utcnow() - timedelta(hours=24)).timestamp()
            logger.info(f"First poll for r/{subreddit_name}, using time_filter='day'")
        
        # Fetch posts - Apify直接返回我们需要的数量，不要本地过滤
        # 使用time_filter让Apify只返回相关时间段的帖子
        all_posts = self.reddit_provider.scrape_subreddit(
            subreddit_name=subreddit_name,
            max_posts=limit,  # 直接限制数量，不要抓100个再过滤
            sort="new",
            time_filter=time_filter  # Apify会过滤时间
        )
        
        # 移除本地时间戳过滤 - 相信Apify的time_filter
        # 这样可以避免浪费API调用费用
        posts = all_posts
        
        logger.info(f"Found {len(posts)} posts in r/{subreddit_name} from Apify (time_filter='{time_filter}')")
        
        # Update poll record
        if poll_record:
            poll_record.last_poll_at = datetime.utcnow()
            poll_record.poll_count += 1
            poll_record.total_posts_found += len(posts)
            if posts:
                poll_record.last_post_timestamp = max(p["created_utc"] for p in posts if p["created_utc"])
        else:
            # Create new poll record
            poll_record = GlobalSubredditPoll(
                subreddit_name=subreddit_name,
                last_poll_at=datetime.utcnow(),
                last_post_timestamp=max(p["created_utc"] for p in posts if p["created_utc"]) if posts else since_timestamp,
                poll_count=1,
                total_posts_found=len(posts)
            )
            db.add(poll_record)
        
        db.commit()
        
        return posts
    
    def distribute_leads(
        self,
        db: Session,
        subreddit_name: str,
        posts: List[Dict[str, Any]]
    ) -> int:
        """
        Distribute posts to relevant campaigns as leads
        Score each post for each campaign
        
        Returns number of leads created
        """
        if not posts:
            return 0
        
        # Find all campaigns watching this subreddit
        campaigns = db.execute(
            select(RedditCampaign).join(
                RedditCampaignSubreddit,
                RedditCampaignSubreddit.campaign_id == RedditCampaign.id
            ).where(
                RedditCampaign.status == RedditCampaignStatus.ACTIVE,
                RedditCampaignSubreddit.subreddit_name == subreddit_name,
                RedditCampaignSubreddit.is_active == True
            )
        ).scalars().all()
        
        if not campaigns:
            logger.info(f"No active campaigns for r/{subreddit_name}")
            return 0
        
        logger.info(f"Distributing {len(posts)} posts to {len(campaigns)} campaigns")
        
        leads_created = 0
        
        for campaign in campaigns:
            logger.info(f"Processing campaign {campaign.id}: {campaign.business_description[:50]}...")
            
            # Score posts for this campaign
            scored_posts = self.scoring_service.batch_score_posts(
                posts=posts,
                business_description=campaign.business_description
            )
            
            # Create leads for relevant posts (score >= 0.5)
            for scored_post in scored_posts:
                if scored_post["relevancy_score"] < 0.5:
                    continue  # Skip low-score posts
                
                # Check if lead already exists
                existing_lead = db.execute(
                    select(RedditLead).where(
                        RedditLead.campaign_id == campaign.id,
                        RedditLead.reddit_post_id == scored_post["id"]
                    )
                ).scalar_one_or_none()
                
                if existing_lead:
                    logger.debug(f"Lead already exists: {scored_post['id']}")
                    continue
                
                # Create new lead
                lead = RedditLead(
                    campaign_id=campaign.id,
                    reddit_post_id=scored_post["id"],
                    subreddit_name=scored_post.get("subreddit_name") or scored_post.get("subreddit"),
                    title=scored_post["title"],
                    content=scored_post.get("content") or scored_post.get("selftext", ""),
                    author=scored_post["author"],
                    post_url=scored_post["url"],
                    score=scored_post["score"],
                    num_comments=scored_post["num_comments"],
                    created_utc=scored_post["created_utc"],
                    relevancy_score=scored_post["relevancy_score"],
                    relevancy_reason=scored_post["relevancy_reason"],
                    suggested_comment=scored_post["suggested_comment"],
                    suggested_dm=scored_post["suggested_dm"],
                    status=RedditLeadStatus.NEW
                )
                db.add(lead)
                leads_created += 1
                
                logger.info(
                    f"Created lead: {scored_post['id']} "
                    f"(score: {scored_post['relevancy_score']:.2f}) "
                    f"for campaign {campaign.id}"
                )
            
            # Update campaign last_poll_at
            campaign.last_poll_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"Created {leads_created} new leads across all campaigns")
        
        return leads_created
    
    def poll_all_active_subreddits(self, db: Session) -> Dict[str, Any]:
        """
        Main polling function: Poll all active subreddits and distribute leads
        This is called by Celery task
        
        Returns summary statistics
        """
        logger.info("Starting centralized Reddit polling")
        
        subreddits_to_poll = self.get_subreddits_to_poll(db)
        
        if not subreddits_to_poll:
            logger.info("No subreddits need polling")
            return {
                "subreddits_polled": 0,
                "total_posts_found": 0,
                "total_leads_created": 0
            }
        
        total_posts = 0
        total_leads = 0
        
        for subreddit_name in subreddits_to_poll:
            try:
                # Poll subreddit
                posts = self.poll_subreddit(db, subreddit_name)
                total_posts += len(posts)

                # Distribute to campaigns
                leads_created = self.distribute_leads(db, subreddit_name, posts)
                total_leads += leads_created

            except Exception as e:
                logger.error(f"Error polling r/{subreddit_name}: {e}", exc_info=True)
                # 回滚失败的事务，确保 session 可以继续使用
                db.rollback()
                continue
        
        summary = {
            "subreddits_polled": len(subreddits_to_poll),
            "total_posts_found": total_posts,
            "total_leads_created": total_leads
        }
        
        logger.info(f"Polling complete: {summary}")
        return summary
    
    def poll_campaign_immediately(self, db: Session, campaign_id: int) -> Dict[str, Any]:
        """
        Poll a specific campaign's subreddits immediately, bypassing time checks
        Used for manual "Run Now" triggers
        
        Args:
            db: Database session
            campaign_id: Campaign to poll
        
        Returns:
            Summary statistics
        """
        logger.info(f"Starting immediate poll for campaign {campaign_id}")
        
        # Get campaign
        campaign = db.get(RedditCampaign, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        if campaign.status != RedditCampaignStatus.ACTIVE:
            raise ValueError(f"Campaign {campaign_id} is not active (status: {campaign.status})")
        
        # Get campaign's active subreddits
        all_subreddits = campaign.subreddits
        subreddits_to_poll = [
            sub.subreddit_name 
            for sub in all_subreddits 
            if sub.is_active
        ]
        
        if not subreddits_to_poll:
            logger.warning(
                f"Campaign {campaign_id} has no active subreddits. "
                f"Total subreddits: {len(all_subreddits)}, "
                f"Active: {sum(1 for sub in all_subreddits if sub.is_active)}"
            )
            return {
                "campaign_id": campaign_id,
                "subreddits_polled": 0,
                "total_posts_found": 0,
                "total_leads_created": 0,
                "message": f"No active subreddits found. Total subreddits: {len(all_subreddits)}"
            }
        
        logger.info(f"Polling {len(subreddits_to_poll)} subreddits for campaign {campaign_id}")
        
        total_posts = 0
        total_leads = 0
        
        for subreddit_name in subreddits_to_poll:
            try:
                # Poll subreddit (ignoring time checks) - 每个subreddit只抓20个帖子
                posts = self.poll_subreddit(db, subreddit_name, limit=20)
                total_posts += len(posts)

                # Distribute leads only to this campaign
                leads_created = self._distribute_leads_to_campaign(
                    db, campaign_id, subreddit_name, posts
                )
                total_leads += leads_created

            except Exception as e:
                logger.error(f"Error polling r/{subreddit_name} for campaign {campaign_id}: {e}", exc_info=True)
                # 回滚失败的事务，确保 session 可以继续使用
                db.rollback()
                continue
        
        summary = {
            "campaign_id": campaign_id,
            "subreddits_polled": len(subreddits_to_poll),
            "total_posts_found": total_posts,
            "total_leads_created": total_leads
        }
        
        logger.info(f"Immediate poll complete for campaign {campaign_id}: {summary}")
        return summary
    
    def _distribute_leads_to_campaign(
        self, 
        db: Session, 
        campaign_id: int,
        subreddit_name: str, 
        posts: List[Dict[str, Any]]
    ) -> int:
        """
        新流程：先保存帖子到数据库，再异步评分
        1. 保存所有新帖子（未评分状态）
        2. 调用LLM评分并更新
        3. 删除不相关的帖子（<30%）
        
        优点：如果LLM出错，已保存的帖子不会丢失
        
        Returns:
            Number of leads created
        """
        if not posts:
            return 0
        
        campaign = db.get(RedditCampaign, campaign_id)
        if not campaign:
            return 0
        
        # Step 1: 先保存所有新帖子（未评分状态）
        new_leads = []
        for post in posts:
            try:
                # Check if lead already exists
                existing_lead = db.execute(
                    select(RedditLead).where(
                        RedditLead.campaign_id == campaign_id,
                        RedditLead.reddit_post_id == post["id"]
                    )
                ).scalar_one_or_none()
                
                if existing_lead:
                    logger.debug(f"Lead already exists for campaign {campaign_id}, post {post['id']}")
                    continue
                
                # 创建未评分的lead（relevancy_score = None）
                lead = RedditLead(
                    campaign_id=campaign_id,
                    reddit_post_id=post["id"],
                    subreddit_name=subreddit_name,
                    title=post["title"],
                    content=post["content"],
                    author=post["author"],
                    post_url=post["url"],
                    score=post["score"],
                    num_comments=post["num_comments"],
                    created_utc=post["created_utc"],
                    relevancy_score=None,  # 待评分
                    relevancy_reason="Pending scoring",
                    suggested_comment="",
                    suggested_dm="",
                    status=RedditLeadStatus.NEW
                )
                
                db.add(lead)
                new_leads.append(lead)
                logger.info(f"Saved post to DB (pending scoring): {post['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error saving post {post.get('id')}: {e}", exc_info=True)
                continue
        
        # Commit后才能获取到lead ID
        db.commit()
        logger.info(f"Saved {len(new_leads)} new posts to database for campaign {campaign_id}")
        
        # Step 2: 对每个新lead进行评分
        scored_count = 0
        kept_count = 0
        
        for lead in new_leads:
            try:
                # 构建post dict用于评分
                post_dict = {
                    "id": lead.reddit_post_id,
                    "title": lead.title,
                    "content": lead.content,
                    "author": lead.author,
                    "url": lead.post_url,
                    "score": lead.score,
                    "num_comments": lead.num_comments,
                    "created_utc": lead.created_utc,
                    "subreddit_name": lead.subreddit_name
                }
                
                logger.debug(f"Scoring post {lead.reddit_post_id} for campaign {campaign_id}")
                score_result = self.scoring_service.score_post(
                    post=post_dict,
                    business_description=campaign.business_description
                )
                
                # 更新评分
                lead.relevancy_score = score_result["relevancy_score"]
                lead.relevancy_reason = score_result["relevancy_reason"]
                lead.suggested_comment = score_result["suggested_comment"]
                lead.suggested_dm = score_result["suggested_dm"]
                
                scored_count += 1
                logger.debug(f"Scored post {lead.reddit_post_id}: {score_result['relevancy_score']}")
                
                # Step 3: 删除不相关的帖子（< 50分）
                if lead.relevancy_score < 50:
                    logger.info(f"Removing low-relevancy post ({lead.relevancy_score}): {lead.title[:50]}")
                    db.delete(lead)
                else:
                    kept_count += 1
                    logger.info(f"Kept relevant post ({lead.relevancy_score}): {lead.title[:50]}")
                
                # 立即写入数据库！不要缓存
                db.commit()
                
            except Exception as e:
                logger.error(f"Error scoring lead {lead.id}: {e}", exc_info=True)
                db.rollback()  # 回滚失败的事务
                # 评分失败的保留在数据库中（relevancy_score = None）
                continue
        
        logger.info(f"Campaign {campaign_id}: Scored {scored_count}/{len(new_leads)} posts, kept {kept_count} relevant leads")
        
        return kept_count

