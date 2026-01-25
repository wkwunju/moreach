"""
Reddit Lead Scoring Prompt Template
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class RedditLeadAnalysis(BaseModel):
    """Reddit 潜在客户分析结果"""
    relevancy_score: int = Field(
        description="Relevancy score: must be EXACTLY one of these values: 100, 90, 80, 70, 60, 50, or 0",
        ge=0,
        le=100
    )
    reason: str = Field(description="1-2 sentence explanation of the score")
    suggested_comment: str = Field(description="2-3 sentence helpful comment")
    suggested_dm: str = Field(description="3-4 sentence direct message")


REDDIT_SCORING_TEMPLATE = """You are analyzing a Reddit post for lead generation potential.

BUSINESS:
{business_description}

REDDIT POST:
Title: {title}
Content: {content}
Subreddit: r/{subreddit_name}
Engagement: {score} upvotes, {num_comments} comments

TASK:
1. Rate relevancy using EXACTLY ONE of these scores (no other values allowed):
   - 100: Perfect match - User is EXPLICITLY asking for recommendations/solutions in this exact industry
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

Return ONLY valid JSON matching this structure:
{{
  "relevancy_score": 100,
  "reason": "User is explicitly asking for recommendations in this exact industry",
  "suggested_comment": "Have you considered...? We've found that... Feel free to check out [solution].",
  "suggested_dm": "Hi! I saw your post... We actually help with this exact problem..."
}}
"""


def create_reddit_scoring_prompt() -> PromptTemplate:
    """创建 Reddit Lead Scoring prompt"""
    return PromptTemplate(
        template=REDDIT_SCORING_TEMPLATE,
        input_variables=[
            "business_description",
            "title",
            "content",
            "subreddit_name",
            "score",
            "num_comments"
        ]
    )


def create_reddit_scoring_parser() -> JsonOutputParser:
    """创建结构化输出解析器"""
    return JsonOutputParser(pydantic_object=RedditLeadAnalysis)

