"""
Reddit Batch Scoring Prompt Template
Scores multiple posts in a single LLM call for cost efficiency.
~66% token reduction compared to individual scoring.
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List


class PostScore(BaseModel):
    """Score for a single post"""
    post_id: str = Field(description="The post ID")
    relevancy_score: int = Field(
        description="Relevancy score: must be EXACTLY one of: 100, 90, 80, 70, 60, 50, or 0",
        ge=0,
        le=100
    )
    reason: str = Field(description="1-2 sentence explanation")


class BatchScoreResult(BaseModel):
    """Batch scoring result - scores for multiple posts"""
    scores: List[PostScore] = Field(description="List of scores for each post")


BATCH_SCORING_TEMPLATE = """You are analyzing multiple Reddit posts for lead generation potential.

BUSINESS:
{business_description}

POSTS TO ANALYZE:
{posts_json}

SCORING GUIDE (use EXACTLY one of these values):
- 100: Perfect - User EXPLICITLY asking for recommendations in this industry
- 90: Excellent - User has clear need/pain point business directly addresses
- 80: Strong - Highly relevant, clear business opportunity
- 70: Good - Related to business area, potential opportunity
- 60: Moderate - Somewhat related, worth reaching out
- 50: Weak - Barely related, minimal connection
- 0: Not a lead - Completely irrelevant or spam

GUIDELINES:
- Asking for product/service recommendations in your industry -> 100
- Specific problem your business solves -> 90
- Be GENEROUS - lean towards higher scores when in doubt
- Only give 0 if completely unrelated

Return JSON with scores for ALL posts:
{{"scores": [
  {{"post_id": "abc123", "relevancy_score": 90, "reason": "User looking for X solution"}},
  {{"post_id": "def456", "relevancy_score": 70, "reason": "Related topic, potential fit"}}
]}}
"""


def create_batch_scoring_prompt() -> PromptTemplate:
    """Create batch scoring prompt for multiple posts"""
    return PromptTemplate(
        template=BATCH_SCORING_TEMPLATE,
        input_variables=["business_description", "posts_json"]
    )


def create_batch_scoring_parser() -> JsonOutputParser:
    """Create structured output parser for batch scoring"""
    return JsonOutputParser(pydantic_object=BatchScoreResult)


def format_posts_for_batch(posts: list) -> str:
    """
    Format posts list into a string for the prompt.
    Keeps only essential info to minimize tokens.
    """
    formatted = []
    for i, post in enumerate(posts):
        post_id = post.get('reddit_post_id') or post.get('id', f'post_{i}')
        title = post.get('title', '')[:200]  # Limit title length
        content = (post.get('content', '') or '')[:500]  # Limit content length
        subreddit = post.get('subreddit_name', '')
        score = post.get('score', 0)
        comments = post.get('num_comments', 0)

        formatted.append(
            f"[{post_id}] r/{subreddit} ({score} pts, {comments} comments)\n"
            f"Title: {title}\n"
            f"Content: {content[:500] if content else '(no content)'}"
        )

    return "\n\n---\n\n".join(formatted)
