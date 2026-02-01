"""
Reddit Quick Scoring Prompt Template
Phase 1: Returns only relevancy_score and reason (no suggestions)
Used for fast batch scoring to reduce LLM costs
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class QuickScoreResult(BaseModel):
    """Quick scoring result - score and reason only"""
    relevancy_score: int = Field(
        description="Relevancy score: must be EXACTLY one of these values: 100, 90, 80, 70, 60, 50, or 0",
        ge=0,
        le=100
    )
    reason: str = Field(description="1-2 sentence explanation of the score")


QUICK_SCORING_TEMPLATE = """You are analyzing a Reddit post for lead generation potential.

BUSINESS:
{business_description}

REDDIT POST:
Title: {title}
Content: {content}
Subreddit: r/{subreddit_name}
Engagement: {score} upvotes, {num_comments} comments

TASK: Rate relevancy using EXACTLY ONE of these scores (no other values allowed):
- 100: Perfect match - User is EXPLICITLY asking for recommendations/solutions in this exact industry
- 90: Excellent lead - User has clear need/pain point that business directly addresses
- 80: Strong lead - Highly relevant to business, clear business opportunity
- 70: Good lead - Related to business area, potential opportunity
- 60: Moderate lead - Somewhat related, worth reaching out
- 50: Weak lead - Barely related but has minimal connection
- 0: Not a lead - Completely irrelevant or spam

IMPORTANT SCORING GUIDELINES:
- If user is asking for product/service recommendations in your industry -> 100
- If user has a specific problem your business solves -> 90
- If topic is highly relevant and there's an opportunity -> 80
- Be GENEROUS - lean towards higher scores when in doubt
- Only give 0 if the post is completely unrelated

Return ONLY valid JSON matching this structure:
{{"relevancy_score": 90, "reason": "User is looking for a solution to X problem which aligns with the business."}}
"""


def create_quick_scoring_prompt() -> PromptTemplate:
    """Create quick scoring prompt (score + reason only)"""
    return PromptTemplate(
        template=QUICK_SCORING_TEMPLATE,
        input_variables=[
            "business_description",
            "title",
            "content",
            "subreddit_name",
            "score",
            "num_comments"
        ]
    )


def create_quick_scoring_parser() -> JsonOutputParser:
    """Create structured output parser for quick scoring"""
    return JsonOutputParser(pydantic_object=QuickScoreResult)
