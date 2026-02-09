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
   - MUST address the author as u/{author} (their actual username) - NEVER use placeholders like [Username] or u/username
   - First sentence: Reference their specific problem/situation
   - Second sentence: Brief mention of how you can help + simple question
   - Keep it friendly and conversational

Return ONLY valid JSON matching this structure:
{{"suggested_comment": "Have you considered...? We've found that... Feel free to check out [solution].", "suggested_dm": "Hey u/{author}! Saw your post about struggling with X - that's a common challenge. We've helped others with exactly this, happy to share some tips if you're interested?"}}
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
