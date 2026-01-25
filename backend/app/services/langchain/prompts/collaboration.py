"""
Collaboration Analysis Prompt Template
"""
from langchain_core.prompts import PromptTemplate


COLLABORATION_ANALYSIS_TEMPLATE = """Analyze collaboration opportunities with this Instagram creator.
Provide a concise 2-3 sentence assessment covering:
1. Brand partnership experience (based on sponsored content indicators)
2. Content style and collaboration formats they excel at
3. Unique value proposition for brand partnerships

Profile:
- Handle: {handle}
- Full Name: {full_name}
- Biography: {biography}
- Business Category: {business_category}
- Followers Count: {followers_count}

Collaboration Indicators:
- Has Brand Mentions: {has_brand_mentions}
- Sponsored Posts: {sponsored_posts}
- Product Showcases: {product_showcases}
- Common Hashtags: {common_hashtags}

{business_context}

Generate a concise collaboration opportunity analysis (2-3 sentences max).
"""


def create_collaboration_analysis_prompt() -> PromptTemplate:
    """创建 Collaboration Analysis prompt"""
    return PromptTemplate(
        template=COLLABORATION_ANALYSIS_TEMPLATE,
        input_variables=[
            "handle",
            "full_name",
            "biography",
            "business_category",
            "followers_count",
            "has_brand_mentions",
            "sponsored_posts",
            "product_showcases",
            "common_hashtags",
            "business_context"
        ]
    )

