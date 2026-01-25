"""
Profile Summary Prompt Template
"""
from langchain_core.prompts import PromptTemplate


PROFILE_SUMMARY_TEMPLATE = """Summarize this Instagram creator in 1-2 sentences.
Focus on lifestyle, interests, location hints, and audience tone.
If data is missing, make no assumptions. Keep it factual.

Profile Information:
- Full Name: {full_name}
- Biography: {biography}
- Business Category: {business_category}
- Hashtags: {hashtags}
- Followers Count: {followers_count}

Recent Post Captions:
{captions}

Generate a concise, neutral summary (1-2 sentences max).
"""


def create_profile_summary_prompt() -> PromptTemplate:
    """创建 Profile Summary prompt"""
    return PromptTemplate(
        template=PROFILE_SUMMARY_TEMPLATE,
        input_variables=[
            "full_name",
            "biography", 
            "business_category",
            "hashtags",
            "followers_count",
            "captions"
        ]
    )

