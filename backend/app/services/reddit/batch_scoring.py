"""
Batch Reddit Lead Scoring Service

Two-phase scoring for efficiency:
- Phase 1: TRUE batch scoring - multiple posts per LLM call (~66% token savings)
- Phase 2: Suggestions (on-demand or top N)
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache

from app.services.langchain.config import get_llm
from app.services.langchain.prompts.reddit_quick_scoring import (
    create_quick_scoring_prompt,
    create_quick_scoring_parser
)
from app.services.langchain.prompts.reddit_batch_scoring import (
    create_batch_scoring_prompt,
    create_batch_scoring_parser,
    format_posts_for_batch
)
from app.services.langchain.prompts.reddit_suggestion import (
    create_suggestion_prompt,
    create_suggestion_parser
)


logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_CONCURRENT = 5
DEFAULT_BATCH_SIZE = 20  # Posts per LLM call
DEFAULT_TOP_N_SUGGESTIONS = 20
ALLOWED_SCORES = [100, 90, 80, 70, 60, 50, 0]
# Auto-generate suggestions only for posts with score >= this threshold
AUTO_SUGGESTION_THRESHOLD = 90


@lru_cache()
def _create_quick_scoring_chain():
    """Create and cache quick scoring chain (for single post fallback)"""
    llm = get_llm()
    prompt = create_quick_scoring_prompt()
    parser = create_quick_scoring_parser()
    return prompt | llm | parser


@lru_cache()
def _create_batch_scoring_chain():
    """Create and cache batch scoring chain (for multiple posts)"""
    llm = get_llm()
    prompt = create_batch_scoring_prompt()
    parser = create_batch_scoring_parser()
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
    - Phase 1: TRUE batch scoring - multiple posts per LLM call
    - Phase 2: Suggestions (on-demand or top N) - concurrent
    """

    def __init__(
        self,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.quick_chain = _create_quick_scoring_chain()
        self.batch_chain = _create_batch_scoring_chain()
        self.suggestion_chain = _create_suggestion_chain()
        # Track LLM calls for usage reporting
        self.llm_calls_made = 0

    async def _score_batch(
        self,
        posts: List[Dict[str, Any]],
        business_description: str,
        semaphore: asyncio.Semaphore
    ) -> List[Dict[str, Any]]:
        """
        Score a batch of posts in a SINGLE LLM call.
        Returns posts with relevancy_score and reason added.
        """
        if not posts:
            return []

        async with semaphore:
            try:
                # Format posts for the prompt
                posts_json = format_posts_for_batch(posts)

                # Create a mapping from post_id to post
                post_map = {}
                for post in posts:
                    post_id = post.get('reddit_post_id') or post.get('id', '')
                    post_map[post_id] = post

                # Run batch scoring chain
                result = await asyncio.to_thread(
                    self.batch_chain.invoke,
                    {
                        "business_description": business_description,
                        "posts_json": posts_json
                    }
                )

                self.llm_calls_made += 1
                logger.info(f"Batch scored {len(posts)} posts in 1 LLM call")

                # Parse results and update posts
                scored_posts = []
                scores_map = {}

                # Build a map of post_id -> score result
                for score_item in result.get("scores", []):
                    scores_map[score_item.get("post_id", "")] = score_item

                # Match scores back to posts
                for post in posts:
                    post_id = post.get('reddit_post_id') or post.get('id', '')
                    score_result = scores_map.get(post_id)

                    if score_result:
                        llm_score = score_result.get("relevancy_score", 50)
                        # Snap to allowed values
                        if llm_score not in ALLOWED_SCORES:
                            llm_score = min(ALLOWED_SCORES, key=lambda x: abs(x - llm_score))

                        scored_posts.append({
                            **post,
                            "relevancy_score": llm_score,
                            "relevancy_reason": score_result.get("reason", ""),
                            "has_suggestions": False
                        })
                    else:
                        # Post not found in results, use default
                        logger.warning(f"Post {post_id} not found in batch results")
                        scored_posts.append({
                            **post,
                            "relevancy_score": 50,
                            "relevancy_reason": "Score not returned",
                            "has_suggestions": False
                        })

                return scored_posts

            except Exception as e:
                logger.error(f"Error batch scoring {len(posts)} posts: {e}")
                # Fall back to default scores for all posts in batch
                return [
                    {
                        **post,
                        "relevancy_score": 50,
                        "relevancy_reason": f"Batch scoring error: {str(e)}",
                        "has_suggestions": False
                    }
                    for post in posts
                ]

    async def _quick_score_single(
        self,
        post: Dict[str, Any],
        business_description: str,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Score a single post (fallback for small batches).
        Returns post dict with relevancy_score and reason added.
        """
        post_id = post.get('reddit_post_id') or post.get('id', 'unknown')

        async with semaphore:
            try:
                content = post.get('content', '') or ''

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

                self.llm_calls_made += 1

                llm_score = result.get("relevancy_score", 50)
                if llm_score not in ALLOWED_SCORES:
                    llm_score = min(ALLOWED_SCORES, key=lambda x: abs(x - llm_score))

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
        Generate suggestions for a single post (Phase 2).
        Returns dict with suggested_comment and suggested_dm.
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
                        "author": post.get("author", ""),
                        "relevancy_reason": post.get("relevancy_reason", "Relevant post")
                    }
                )

                self.llm_calls_made += 1
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
        Phase 1: TRUE batch scoring - multiple posts per LLM call.

        Instead of 1 LLM call per post, we batch posts together:
        - 99 posts with batch_size=10 = ~10 LLM calls (not 99!)
        - ~66% token savings from shared system prompt

        Args:
            posts: List of post dicts
            business_description: Business description for scoring
            on_progress: Optional callback(current, total) for progress updates

        Returns:
            List of scored post dicts with relevancy_score, relevancy_reason, has_suggestions
        """
        if not posts:
            return []

        self.llm_calls_made = 0  # Reset counter
        total_posts = len(posts)
        num_batches = (total_posts + self.batch_size - 1) // self.batch_size

        logger.info(
            f"Batch scoring {total_posts} posts in {num_batches} batches "
            f"(batch_size={self.batch_size}, max_concurrent={self.max_concurrent})"
        )

        # Split posts into batches
        batches = [
            posts[i:i + self.batch_size]
            for i in range(0, total_posts, self.batch_size)
        ]

        semaphore = asyncio.Semaphore(self.max_concurrent)
        scored_posts = []
        posts_processed = 0

        async def score_batch_with_progress(batch: List[Dict], batch_index: int):
            nonlocal posts_processed
            results = await self._score_batch(batch, business_description, semaphore)
            posts_processed += len(batch)
            if on_progress:
                on_progress(posts_processed, total_posts)
            return results

        # Process batches concurrently
        tasks = [
            score_batch_with_progress(batch, i)
            for i, batch in enumerate(batches)
        ]

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for batch_index, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Batch {batch_index} failed: {result}")
                # Add default scores for failed batch
                for post in batches[batch_index]:
                    scored_posts.append({
                        **post,
                        "relevancy_score": 50,
                        "relevancy_reason": f"Batch error: {str(result)}",
                        "has_suggestions": False
                    })
            else:
                scored_posts.extend(result)

        logger.info(
            f"Batch scoring complete: {len(scored_posts)} posts scored "
            f"with {self.llm_calls_made} LLM calls (saved {total_posts - self.llm_calls_made} calls)"
        )

        return scored_posts

    def get_llm_calls_made(self) -> int:
        """Return the number of LLM calls made in the last batch operation"""
        return self.llm_calls_made

    async def generate_suggestions_for_high_score(
        self,
        scored_posts: List[Dict[str, Any]],
        business_description: str,
        min_score: int = AUTO_SUGGESTION_THRESHOLD,
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Auto-generate suggestions ONLY for high-scoring posts (90+).
        Lower-scoring posts get suggestions generated on-demand when user clicks.

        Args:
            scored_posts: List of already-scored post dicts
            business_description: Business description
            min_score: Minimum score threshold for auto-generation (default: 90)
            on_progress: Optional callback(current, total) for progress updates

        Returns:
            Same list with suggestions added to high-scoring posts only
        """
        sorted_posts = sorted(
            scored_posts,
            key=lambda x: x.get("relevancy_score", 0),
            reverse=True
        )

        posts_needing_suggestions = [
            p for p in sorted_posts
            if p.get("relevancy_score", 0) >= min_score
        ]

        logger.info(
            f"Auto-generating suggestions for {len(posts_needing_suggestions)} "
            f"high-score (>={min_score}) posts"
        )

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

        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                posts_needing_suggestions[i]["suggested_comment"] = result.get("suggested_comment", "")
                posts_needing_suggestions[i]["suggested_dm"] = result.get("suggested_dm", "")
                posts_needing_suggestions[i]["has_suggestions"] = True

        logger.info(
            f"Auto-suggestion generation complete for {len(posts_needing_suggestions)} posts"
        )
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
        Kept for backward compatibility.
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
        On-demand suggestion generation for a single post.
        Called when user clicks into a lead that doesn't have suggestions.

        Args:
            post: Post dict with title, content, subreddit_name, relevancy_reason
            business_description: Business description

        Returns:
            Dict with suggested_comment and suggested_dm
        """
        semaphore = asyncio.Semaphore(1)
        return await self._generate_suggestion_single(post, business_description, semaphore)


# Convenience functions for sync usage
def batch_quick_score_sync(
    posts: List[Dict[str, Any]],
    business_description: str,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> tuple[List[Dict[str, Any]], int]:
    """
    Synchronous wrapper for batch quick scoring.
    Returns (scored_posts, llm_calls_made)
    """
    service = BatchScoringService(max_concurrent=max_concurrent, batch_size=batch_size)
    results = asyncio.run(service.batch_quick_score(posts, business_description))
    return results, service.get_llm_calls_made()


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
