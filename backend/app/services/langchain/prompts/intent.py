"""
Intent Parsing Prompt Template
"""
from langchain_core.prompts import PromptTemplate


INTENT_TEMPLATE = """Extract a concise influencer discovery intent from the business description and constraints.
Return a short plain-text query phrase.

Description: {description}
Constraints: {constraints}

Think about:
- What industry or niche is being targeted?
- What location or geographic focus?
- What are the key requirements?

Output a short, clear search query (1-2 sentences max).
"""


def create_intent_prompt() -> PromptTemplate:
    """创建 Intent 解析 prompt"""
    return PromptTemplate(
        template=INTENT_TEMPLATE,
        input_variables=["description", "constraints"]
    )

