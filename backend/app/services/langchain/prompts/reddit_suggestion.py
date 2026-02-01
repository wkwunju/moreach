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
    suggested_dm: str = Field(description="3-4 sentence personalized direct message")


SUGGESTION_TEMPLATE = """Generate outreach content for this Reddit lead.

BUSINESS:
{business_description}

REDDIT POST:
Title: {title}
Content: {content}
Subreddit: r/{subreddit_name}
Relevancy Analysis: {relevancy_reason}

TASK:
1. Generate a helpful, non-promotional comment (2-3 sentences):
   - Add value first, mention your solution naturally
   - Don't be too salesy
   - Include a subtle call-to-action

2. Generate a direct message (3-4 sentences):
   - More direct but still value-focused
   - Personalize based on their specific situation
   - Reference their specific problem or question

Return ONLY valid JSON matching this structure:
{{"suggested_comment": "Have you considered...? We've found that... Feel free to check out [solution].", "suggested_dm": "Hi! I saw your post about... We actually help with this exact problem..."}}
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
            "relevancy_reason"
        ]
    )


def create_suggestion_parser() -> JsonOutputParser:
    """Create structured output parser for suggestions"""
    return JsonOutputParser(pydantic_object=SuggestionResult)
