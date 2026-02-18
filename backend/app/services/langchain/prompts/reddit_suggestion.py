"""
Reddit Suggestion Generation Prompt Template
Phase 2: Generates suggested_comment and suggested_dm only
Called on-demand for top N posts or when user clicks a lead

Supports per-campaign custom prompts via {comment_instructions} and {dm_instructions}.
"""
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class SuggestionResult(BaseModel):
    """Suggestion generation result - comment and DM only"""
    suggested_comment: str = Field(description="2-3 sentence helpful comment")
    suggested_dm: str = Field(description="2 sentence friendly direct message")


# Default instructions when campaign has no custom prompts
DEFAULT_COMMENT_INSTRUCTIONS = """   - Directly answer their question or address their problem with actionable advice (2-3 sentences)
   - Share specific tips, techniques, or approaches that would genuinely help
   - Sound like a knowledgeable community member, NOT a business
   - Do NOT mention your product, service, company, or anything promotional
   - Do NOT include any call-to-action or links
   - Focus purely on being helpful — the goal is to build trust and credibility"""

DEFAULT_DM_INSTRUCTIONS = """   - Start with just "Hey!" - do NOT include the username (no u/username, no [Username])
   - First sentence: Reference their specific post and the concrete problem they're facing
   - Second sentence: Clearly state what you offer and how it directly solves their problem, then ask if they'd like to try it or learn more
   - Be direct and specific about your product/service - don't be vague like "share some insights" or "happy to help"
   - Keep it friendly but get to the point"""


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
1. Generate a comment:
{comment_instructions}

2. Generate a direct message (2 sentences):
{dm_instructions}

Return ONLY valid JSON matching this structure:
{{"suggested_comment": "Your helpful comment here.", "suggested_dm": "Hey! Your DM here."}}
"""


def create_suggestion_prompt() -> PromptTemplate:
    """Create suggestion generation prompt with customizable instructions"""
    return PromptTemplate(
        template=SUGGESTION_TEMPLATE,
        input_variables=[
            "business_description",
            "title",
            "content",
            "subreddit_name",
            "author",
            "relevancy_reason",
            "comment_instructions",
            "dm_instructions",
        ]
    )


def create_suggestion_parser() -> JsonOutputParser:
    """Create structured output parser for suggestions"""
    return JsonOutputParser(pydantic_object=SuggestionResult)
