"""
Batch Reddit Lead Scoring Service

Two-phase scoring for efficiency:
- Phase 1: Quick score (relevancy_score + reason) - runs concurrently
- Phase 2: Suggestions (on-demand or top N)
"""
import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
from functools import lru_cache

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.reddit_quick_scoring import (
    create_quick_scoring_prompt,
    create_quick_scoring_parser
)
from app.services.langchain.prompts.reddit_suggestion import (
    create_suggestion_prompt,
    create_suggestion_parser
)


logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_CONCURRENT = 5
DEFAULT_TOP_N_SUGGESTIONS = 20
ALLOWED_SCORES = [100, 90, 80, 70, 60, 50, 0]
# Auto-generate suggestions only for posts with score >= this threshold
AUTO_SUGGESTION_THRESHOLD = 90


@lru_cache()
def _create_quick_scoring_chain():
    """Create and cache quick scoring chain"""
    llm = get_llm()
    prompt = create_quick_scoring_prompt()
    parser = create_quick_scoring_parser()
    return prompt | llm | parser


@lru_cache()
def _create_suggestion_chain():
    """Create and cache suggestion generation chain"""
    llm = get_llm()
    prompt = create_suggestion_prompt()
    parser = create_suggestion_parser()
    return prompt | llm | parser


class BatchScoringService:
    """
    Two-phase scoring service for Reddit leads:
    - Phase 1: Quick score (relevancy_score + reason) - concurrent
    - Phase 2: Suggestions (on-demand or top N) - concurrent
    """

    def __init__(self, max_concurrent: int = DEFAULT_MAX_CONCURRENT):
        self.max_concurrent = max_concurrent
        self.quick_chain = _create_quick_scoring_chain()
        self.suggestion_chain = _create_suggestion_chain()

    async def _quick_score_single(
        self,
        post: Dict[str, Any],
        business_description: str,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Score a single post (Phase 1)
        Returns post dict with relevancy_score and reason added
        """
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')

        async with semaphore:
            try:
                content = post.get('content', '') or ''

                # Run sync chain in thread pool
                result = await asyncio.to_thread(
                    self.quick_chain.invoke,
                    {
                        "business_description": business_description,
                        "title": post.get("title", ""),
                        "content": content[:1000],
                        "subreddit_name": post.get("subreddit_name", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0)
                    }
                )

                # Validate and snap score to allowed values
                llm_score = result.get("relevancy_score", 50)
                if llm_score not in ALLOWED_SCORES:
                    llm_score = min(ALLOWED_SCORES, key=lambda x: abs(x - llm_score))
                    logger.warning(f"Post {post_id}: LLM returned invalid score, snapped to {llm_score}")

                logger.info(f"Quick scored post {post_id}: {llm_score}")

                return {
                    **post,
                    "relevancy_score": llm_score,
                    "relevancy_reason": result.get("reason", ""),
                    "has_suggestions": False
                }

            except Exception as e:
                logger.error(f"Error quick scoring post {post_id}: {e}")
                return {
                    **post,
                    "relevancy_score": 50,
                    "relevancy_reason": f"Scoring error: {str(e)}",
                    "has_suggestions": False
                }

    async def _generate_suggestion_single(
        self,
        post: Dict[str, Any],
        business_description: str,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, str]:
        """
        Generate suggestions for a single post (Phase 2)
        Returns dict with suggested_comment and suggested_dm
        """
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')

        async with semaphore:
            try:
                content = post.get('content', '') or ''

                result = await asyncio.to_thread(
                    self.suggestion_chain.invoke,
                    {
                        "business_description": business_description,
                        "title": post.get("title", ""),
                        "content": content[:1000],
                        "subreddit_name": post.get("subreddit_name", ""),
                        "relevancy_reason": post.get("relevancy_reason", "Relevant post")
                    }
                )

                logger.info(f"Generated suggestions for post {post_id}")

                return {
                    "suggested_comment": result.get("suggested_comment", ""),
                    "suggested_dm": result.get("suggested_dm", "")
                }

            except Exception as e:
                logger.error(f"Error generating suggestions for post {post_id}: {e}")
                return {
                    "suggested_comment": "",
                    "suggested_dm": ""
                }

    async def batch_quick_score(
        self,
        posts: List[Dict[str, Any]],
        business_description: str,
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Concurrent quick scoring for all posts

        Args:
            posts: List of post dicts
            business_description: Business description for scoring
            on_progress: Optional callback(current, total) for progress updates

        Returns:
            List of scored post dicts with relevancy_score, relevancy_reason, has_suggestions
        """
        logger.info(f"Batch quick scoring {len(posts)} posts with max {self.max_concurrent} concurrent")

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def score_with_progress(post: Dict, index: int):
            result = await self._quick_score_single(post, business_description, semaphore)
            if on_progress:
                on_progress(index + 1, len(posts))
            return result

        tasks = [
            score_with_progress(post, i)
            for i, post in enumerate(posts)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that weren't caught
        scored_posts = []
        for post, result in zip(posts, results):
            if isinstance(result, Exception):
                logger.error(f"Unhandled exception scoring post: {result}")
                scored_posts.append({
                    **post,
                    "relevancy_score": 50,
                    "relevancy_reason": f"Error: {str(result)}",
                    "has_suggestions": False
                })
            else:
                scored_posts.append(result)

        logger.info(f"Batch quick scoring complete: {len(scored_posts)} posts scored")
        return scored_posts

    async def generate_suggestions_for_high_score(
        self,
        scored_posts: List[Dict[str, Any]],
        business_description: str,
        min_score: int = AUTO_SUGGESTION_THRESHOLD,
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Auto-generate suggestions ONLY for high-scoring posts (90+)
        Lower-scoring posts get suggestions generated on-demand when user clicks.

        Args:
            scored_posts: List of already-scored post dicts
            business_description: Business description
            min_score: Minimum score threshold for auto-generation (default: 90)
            on_progress: Optional callback(current, total) for progress updates

        Returns:
            Same list with suggestions added to high-scoring posts only
        """
        # Sort by relevancy_score descending
        sorted_posts = sorted(
            scored_posts,
            key=lambda x: x.get("relevancy_score", 0),
            reverse=True
        )

        # Only auto-generate for posts with score >= 90 (high-value leads)
        # Other posts will get suggestions on-demand when user clicks
        posts_needing_suggestions = [
            p for p in sorted_posts
            if p.get("relevancy_score", 0) >= min_score
        ]

        logger.info(f"Auto-generating suggestions for {len(posts_needing_suggestions)} high-score (>={min_score}) posts")

        if not posts_needing_suggestions:
            return sorted_posts

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def generate_with_progress(post: Dict, index: int):
            suggestions = await self._generate_suggestion_single(
                post, business_description, semaphore
            )
            if on_progress:
                on_progress(index + 1, len(posts_needing_suggestions))
            return suggestions

        tasks = [
            generate_with_progress(post, i)
            for i, post in enumerate(posts_needing_suggestions)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update posts with suggestions
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                posts_needing_suggestions[i]["suggested_comment"] = result.get("suggested_comment", "")
                posts_needing_suggestions[i]["suggested_dm"] = result.get("suggested_dm", "")
                posts_needing_suggestions[i]["has_suggestions"] = True

        logger.info(f"Auto-suggestion generation complete for {len(posts_needing_suggestions)} high-score posts")
        return sorted_posts

    async def generate_suggestions_for_top_n(
        self,
        scored_posts: List[Dict[str, Any]],
        business_description: str,
        top_n: int = DEFAULT_TOP_N_SUGGESTIONS,
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Use generate_suggestions_for_high_score instead.
        Kept for backward compatibility - now delegates to high_score method.
        """
        return await self.generate_suggestions_for_high_score(
            scored_posts, business_description,
            min_score=AUTO_SUGGESTION_THRESHOLD,
            on_progress=on_progress
        )

    async def generate_suggestion_on_demand(
        self,
        post: Dict[str, Any],
        business_description: str
    ) -> Dict[str, str]:
        """
        On-demand suggestion generation for a single post
        Called when user clicks into a lead that doesn't have suggestions

        Args:
            post: Post dict with title, content, subreddit_name, relevancy_reason
            business_description: Business description

        Returns:
            Dict with suggested_comment and suggested_dm
        """
        semaphore = asyncio.Semaphore(1)  # No concurrency limit for single request
        return await self._generate_suggestion_single(post, business_description, semaphore)


# Convenience functions for sync usage
def batch_quick_score_sync(
    posts: List[Dict[str, Any]],
    business_description: str,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
) -> List[Dict[str, Any]]:
    """Synchronous wrapper for batch quick scoring"""
    service = BatchScoringService(max_concurrent=max_concurrent)
    return asyncio.run(service.batch_quick_score(posts, business_description))


def generate_suggestions_sync(
    scored_posts: List[Dict[str, Any]],
    business_description: str,
    top_n: int = DEFAULT_TOP_N_SUGGESTIONS,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
) -> List[Dict[str, Any]]:
    """Synchronous wrapper for top N suggestion generation"""
    service = BatchScoringService(max_concurrent=max_concurrent)
    return asyncio.run(
        service.generate_suggestions_for_top_n(scored_posts, business_description, top_n)
    )


def generate_suggestion_on_demand_sync(
    post: Dict[str, Any],
    business_description: str
) -> Dict[str, str]:
    """Synchronous wrapper for on-demand suggestion generation"""
    service = BatchScoringService()
    return asyncio.run(service.generate_suggestion_on_demand(post, business_description))
