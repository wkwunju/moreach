"""
Reddit Suggestion Generation Prompt Template
Phase 2: Generates suggested_comment and suggested_dm only
Called on-demand for top N posts or when user clicks a lead
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class SuggestionResult(BaseModel):
    """Suggestion generation result - comment and DM only"""
    suggested_comment: str = Field(description="2-3 sentence helpful, non-promotional comment")
    suggested_dm: str = Field(description="2 sentence friendly direct message")


SUGGESTION_TEMPLATE = """Generate outreach content for this Reddit lead.

BUSINESS:
{business_description}

REDDIT POST:
Title: {title}
Content: {content}
Subreddit: r/{subreddit_name}
Author: u/{author}
Relevancy Analysis: {relevancy_reason}

TASK:
1. Generate a helpful, non-promotional comment (2-3 sentences):
   - Add value first, mention your solution naturally
   - Don't be too salesy
   - Include a subtle call-to-action

2. Generate a direct message (2 sentences):
   - Start with just "Hey!" - do NOT include the username (no u/username, no [Username])
   - First sentence: Reference their specific post and the concrete problem they're facing
   - Second sentence: Clearly state what you offer and how it directly solves their problem, then ask if they'd like to try it or learn more
   - Be direct and specific about your product/service - don't be vague like "share some insights" or "happy to help"
   - Keep it friendly but get to the point

Return ONLY valid JSON matching this structure:
{{"suggested_comment": "Have you considered...? We've found that... Feel free to check out [solution].", "suggested_dm": "Hey! Saw your post about struggling with X. We built [product] that does exactly Y - want me to set you up with a demo?"}}
"""


def create_suggestion_prompt() -> PromptTemplate:
    """Create suggestion generation prompt"""
    return PromptTemplate(
        template=SUGGESTION_TEMPLATE,
        input_variables=[
            "business_description",
            "title",
            "content",
            "subreddit_name",
            "author",
            "relevancy_reason"
        ]
    )


def create_suggestion_parser() -> JsonOutputParser:
    """Create structured output parser for suggestions"""
    return JsonOutputParser(pydantic_object=SuggestionResult)
