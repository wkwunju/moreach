"""
Rescore existing Reddit leads that failed to score
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.tables import RedditLead, RedditCampaign
from app.services.reddit.scoring import RedditScoringService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rescore_campaign_leads(campaign_id: int):
    """Rescore all leads for a campaign that have no score"""
    db: Session = SessionLocal()
    
    try:
        # Get campaign
        campaign = db.get(RedditCampaign, campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return
        
        logger.info(f"Rescoring leads for campaign: {campaign.business_description[:100]}")
        
        # Get all leads without scores
        leads = db.query(RedditLead).filter(
            RedditLead.campaign_id == campaign_id,
            RedditLead.relevancy_score.is_(None)
        ).all()
        
        logger.info(f"Found {len(leads)} leads without scores")
        
        if not leads:
            logger.info("No leads to rescore")
            return
        
        # Initialize scoring service
        scoring_service = RedditScoringService()
        
        # Score each lead
        scored_count = 0
        deleted_count = 0
        
        for i, lead in enumerate(leads, 1):
            try:
                logger.info(f"[{i}/{len(leads)}] Scoring: {lead.title[:60]}...")
                
                # Build post dict
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
                
                # Score the post
                score_result = scoring_service.score_post(
                    post=post_dict,
                    business_description=campaign.business_description
                )
                
                # Update lead
                lead.relevancy_score = score_result["relevancy_score"]
                lead.relevancy_reason = score_result["relevancy_reason"]
                lead.suggested_comment = score_result["suggested_comment"]
                lead.suggested_dm = score_result["suggested_dm"]
                
                scored_count += 1
                
                # Delete low-relevancy leads (< 0.3)
                if lead.relevancy_score < 0.3:
                    logger.info(f"  ❌ Score: {lead.relevancy_score:.2f} - DELETING (too low)")
                    db.delete(lead)
                    deleted_count += 1
                else:
                    logger.info(f"  ✅ Score: {lead.relevancy_score:.2f} - KEEPING")
                
                # Commit every 10 leads
                if i % 10 == 0:
                    db.commit()
                    logger.info(f"Progress: {i}/{len(leads)} - Scored: {scored_count}, Deleted: {deleted_count}")
                
            except Exception as e:
                logger.error(f"Error scoring lead {lead.id}: {e}", exc_info=True)
                continue
        
        # Final commit
        db.commit()
        
        logger.info("=" * 80)
        logger.info(f"Rescoring complete!")
        logger.info(f"  Total leads processed: {len(leads)}")
        logger.info(f"  Successfully scored: {scored_count}")
        logger.info(f"  Deleted (low relevancy): {deleted_count}")
        logger.info(f"  Kept (relevant): {scored_count - deleted_count}")
        logger.info("=" * 80)
        
    finally:
        db.close()


def rescore_all_unscored():
    """Rescore all leads across all campaigns that have no score"""
    db: Session = SessionLocal()
    
    try:
        # Get all campaigns with unscored leads
        campaigns = db.query(RedditCampaign).all()
        
        for campaign in campaigns:
            unscored_count = db.query(RedditLead).filter(
                RedditLead.campaign_id == campaign.id,
                RedditLead.relevancy_score.is_(None)
            ).count()
            
            if unscored_count > 0:
                logger.info(f"\nCampaign {campaign.id}: {unscored_count} unscored leads")
                rescore_campaign_leads(campaign.id)
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Rescore specific campaign
        campaign_id = int(sys.argv[1])
        rescore_campaign_leads(campaign_id)
    else:
        # Rescore all campaigns
        rescore_all_unscored()

