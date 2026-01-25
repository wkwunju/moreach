"""
Reddit Lead Scoring Service
Implements a FUNNEL approach to save costs:
1. Python Keyword Match (FREE) - Filter out obviously irrelevant posts
2. LLM Analysis (PAID) - Analyze only filtered posts

This ensures we don't send every post to OpenAI/Gemini
"""
import logging
import json
import re
from typing import Dict, Any, Tuple, Optional

from app.core.config import settings
from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class RedditScoringService:
    """
    Scores Reddit posts for lead potential using a cost-efficient funnel approach
    """
    
    def __init__(self):
        # 根据配置选择 LLM 实现
        if settings.use_langchain_chains:
            from app.services.langchain.chains.reddit_scoring_chain import RedditScoringChainService
            self.llm_scorer = RedditScoringChainService()
            self.use_langchain = True
            logger.info("Using LangChain for Reddit scoring")
        else:
            self.llm_client = get_llm_client()
            self.use_langchain = False
            logger.info("Using legacy LLM client for Reddit scoring")
    
    def extract_keywords(self, business_description: str) -> Dict[str, list]:
        """
        Extract keywords from business description for filtering
        Returns positive (must match) and negative (exclude) keywords
        """
        # This could be enhanced with LLM, but keeping it simple to save costs
        words = business_description.lower().split()
        
        # Remove common words
        stop_words = {
            "i", "we", "our", "us", "the", "a", "an", "for", "to", "of", "in", 
            "on", "at", "by", "with", "from", "is", "are", "am", "and", "or"
        }
        
        keywords = [
            word.strip(".,!?;:") 
            for word in words 
            if len(word) > 3 and word not in stop_words
        ]
        
        # 移除 negative keywords - 让LLM来判断是否是spam/meme
        # 关键词过滤太严格，会误杀正常的营销/推广讨论帖
        negative_keywords = []
        
        return {
            "positive": keywords[:10],  # Top 10 keywords
            "negative": negative_keywords  # 空列表，不过滤
        }
    
    def keyword_filter(
        self, 
        post: Dict[str, Any], 
        keywords: Dict[str, list]
    ) -> Tuple[bool, float, str]:
        """
        Fast keyword-based filtering (FREE)
        
        Returns:
            (should_analyze, keyword_score, reason)
        """
        text = f"{post['title']} {post['content']}".lower()
        
        # 添加调试日志
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')
        logger.debug(f"Filtering post {post_id}: {post.get('title', '')[:50]}")
        logger.debug(f"Positive keywords: {keywords['positive']}")
        logger.debug(f"Post text (first 100 chars): {text[:100]}")
        
        # 移除negative keywords检查 - 让所有帖子都进入LLM分析
        # 不再在这里过滤，由LLM智能判断相关性
        
        # Check positive keywords (仅用于提升评分，不用于排除)
        positive_matches = sum(1 for kw in keywords["positive"] if kw in text)
        logger.debug(f"Post {post_id}: {positive_matches} keyword matches")
        
        # 所有帖子都允许进入LLM分析
        if positive_matches == 0:
            logger.info(f"No keyword matches, using LLM to judge relevancy: {post.get('title', '')[:50]}")
            return True, 0.1, "No keyword matches, using LLM only"
        
        # Calculate simple keyword score (0-1) - 用于辅助LLM评分
        keyword_score = min(positive_matches / len(keywords["positive"]), 1.0)
        return True, keyword_score, f"Matched {positive_matches} keywords"
    
    def llm_analyze(
        self, 
        post: Dict[str, Any], 
        business_description: str,
        keyword_score: float
    ) -> Tuple[float, str, str, str]:
        """
        Deep LLM analysis (PAID - only for filtered posts)
        
        Returns:
            (relevancy_score, reason, suggested_comment, suggested_dm)
        """
        # 使用 LangChain 实现（如果启用）
        if self.use_langchain:
            return self.llm_scorer.llm_analyze(post, business_description, keyword_score)
        
        # 原有实现
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')
        logger.info(f"LLM analyzing post: {post_id}")
        
        prompt = f"""You are analyzing a Reddit post for lead generation potential.

BUSINESS:
{business_description}

REDDIT POST:
Title: {post['title']}
Content: {post.get('content', '')[:1000]}  # Limit to 1000 chars
Subreddit: r/{post.get('subreddit_name', '')}
Engagement: {post['score']} upvotes, {post['num_comments']} comments

TASK:
1. Rate relevancy using EXACTLY ONE of these scores (no other values allowed):
   - 100: Perfect match - User is EXPLICITLY asking for recommendations or solutions in this exact industry
   - 90: Excellent lead - User has clear need/pain point that business directly addresses
   - 80: Strong lead - Highly relevant to business, clear business opportunity
   - 70: Good lead - Related to business area, potential opportunity
   - 60: Moderate lead - Somewhat related, worth reaching out
   - 50: Weak lead - Barely related but has minimal connection
   - 0: Not a lead - Completely irrelevant or spam

IMPORTANT SCORING GUIDELINES:
- If user is asking for product/service recommendations in your industry → 100
- If user has a specific problem your business solves → 90
- If topic is highly relevant and there's an opportunity → 80
- Be GENEROUS - lean towards higher scores when in doubt
- Only give 0 if the post is completely unrelated

2. Explain why in 1-2 sentences

3. Generate a helpful, non-promotional comment (2-3 sentences)
   - Add value first, mention your solution naturally
   - Don't be too salesy
   - Include a subtle call-to-action

4. Generate a direct message (3-4 sentences)
   - More direct but still value-focused
   - Personalize based on their specific situation

Return ONLY valid JSON (no markdown, no extra text):
{{
  "relevancy_score": 100,
  "reason": "User is explicitly asking for recommendations in this exact industry",
  "suggested_comment": "Have you considered...? We've found that... Feel free to check out [solution].",
  "suggested_dm": "Hi! I saw your post... We actually help with this exact problem..."
}}"""

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.llm_client.chat(messages, temperature=0.3)
            
            # Extract text
            if isinstance(response, dict):
                text = response.get("text") or response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                text = str(response)
            
            # Clean up potential markdown formatting
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            result = json.loads(text)
            
            # Get LLM score (should be one of: 100, 90, 80, 70, 60, 50, 0)
            llm_score = result.get("relevancy_score", 50)
            
            # Validate and snap to allowed tiers
            allowed_scores = [100, 90, 80, 70, 60, 50, 0]
            if llm_score not in allowed_scores:
                # Find closest allowed score
                llm_score = min(allowed_scores, key=lambda x: abs(x - llm_score))
                logger.warning(f"LLM returned invalid score, snapped to {llm_score}")
            
            # Return the tier score directly (no blending, no normalization)
            return (
                llm_score,
                result.get("reason", ""),
                result.get("suggested_comment", ""),
                result.get("suggested_dm", "")
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {text[:500]}")
            return 50, "LLM analysis failed - JSON parse error", "", ""
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return 50, f"Analysis error: {str(e)}", "", ""
    
    def score_post(
        self, 
        post: Dict[str, Any], 
        business_description: str,
        keywords: Optional[Dict[str, list]] = None
    ) -> Dict[str, Any]:
        """
        Full scoring pipeline: Keyword Filter -> LLM Analysis
        
        Returns scored post with analysis
        """
        # Extract keywords if not provided
        if keywords is None:
            keywords = self.extract_keywords(business_description)
        
        # Stage 1: Keyword filter (FREE)
        should_analyze, keyword_score, filter_reason = self.keyword_filter(post, keywords)
        
        if not should_analyze:
            post_id = post.get('reddit_post_id') or post.get('id', 'unknown')
            logger.info(f"Post {post_id} filtered out: {filter_reason}")
            return {
                **post,
                "relevancy_score": 0,  # Filtered posts get 0
                "relevancy_reason": f"Filtered: {filter_reason}",
                "suggested_comment": "",
                "suggested_dm": "",
                "passed_filter": False
            }
        
        # Stage 2: LLM analysis (PAID - only for filtered posts)
        relevancy_score, reason, comment, dm = self.llm_analyze(
            post, 
            business_description,
            keyword_score  # Not used anymore but kept for backward compatibility
        )
        
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')
        logger.info(
            f"Post {post_id} scored {relevancy_score:.2f}: {reason}"
        )
        
        scored_result = {
            **post,
            "relevancy_score": relevancy_score,
            "relevancy_reason": reason,
            "suggested_comment": comment,
            "suggested_dm": dm,
            "passed_filter": True
        }
        
        # DEBUG: Verify data preservation
        logger.debug(f"DEBUG Scoring - Post {post_id}: author={scored_result.get('author')}, "
                    f"score={scored_result.get('score')}, num_comments={scored_result.get('num_comments')}")
        
        return scored_result
    
    def batch_score_posts(
        self,
        posts: list[Dict[str, Any]],
        business_description: str
    ) -> list[Dict[str, Any]]:
        """
        Score multiple posts efficiently
        Only sends filtered posts to LLM to save costs
        """
        logger.info(f"Batch scoring {len(posts)} posts")
        
        # Extract keywords once
        keywords = self.extract_keywords(business_description)
        
        scored_posts = []
        llm_analyzed_count = 0
        
        for post in posts:
            scored_post = self.score_post(post, business_description, keywords)
            scored_posts.append(scored_post)
            
            if scored_post.get("passed_filter", False):
                llm_analyzed_count += 1
        
        logger.info(
            f"Batch scoring complete: {llm_analyzed_count}/{len(posts)} posts sent to LLM"
        )
        
        return scored_posts

