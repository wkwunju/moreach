"""
Audience Analysis Prompt Template
"""
from langchain_core.prompts import PromptTemplate


AUDIENCE_ANALYSIS_TEMPLATE = """Analyze the target audience for this Instagram creator based on their profile and recent posts.
Provide a concise 2-3 sentence analysis covering:
1. Primary demographic (age range, lifestyle, interests)
2. Audience values and motivations
3. Geographic focus if evident

Be specific and factual. If information is unclear, state that explicitly.

Profile:
- Full Name: {full_name}
- Biography: {biography}
- Business Category: {business_category}
- Followers Count: {followers_count}
- Hashtags: {hashtags}

Recent Posts:
{post_data}

Generate a concise audience analysis (2-3 sentences max).
"""


def create_audience_analysis_prompt() -> PromptTemplate:
    """创建 Audience Analysis prompt"""
    return PromptTemplate(
        template=AUDIENCE_ANALYSIS_TEMPLATE,
        input_variables=[
            "full_name",
            "biography",
            "business_category",
            "followers_count",
            "hashtags",
            "post_data"
        ]
    )

