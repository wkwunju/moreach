"""
Google Dork Generator Prompt Template
"""
from langchain_core.prompts import PromptTemplate


GOOGLE_DORK_TEMPLATE = """Generate ONE optimized Google search query for Instagram influencer discovery.
Your job is to turn the user's intent into a WORKING dork that returns results.

Follow these rules strictly:
1. Start with site:instagram.com/*/ to target profile headers.
2. If the niche is a product category (e.g., eyewear), avoid the literal product word and instead use adjacent lifestyle/interest terms. Do NOT just echo the input words.
3. Geography handling:
   - If a specific country is given, include that country and its top 5 most populous cities (grouped).
   - If a region is given (e.g., Western Europe), expand it into representative countries and major cities across that region. Do NOT include the raw region term if it is too broad to yield results.
   - If geography is missing, omit geography entirely.
4. Follower range: include ONLY if explicitly specified.
4a. When a follower range is specified, express it as a numeric range phrase like "1000..10000 followers". Do NOT use shorthand like 10k/20k.
5. Contact footprint: include ONLY if explicitly requested; otherwise omit it.
6. Exclude post/media pages: -inurl:"/p/" -inurl:"/reel/" -inurl:"/reels/" -inurl:"/tv/".
7. Use parentheses for every OR group, and avoid mixing OR/AND without grouping.
8. Output ONLY the raw search string. No explanations.

Description: {description}
Constraints: {constraints}

Generate the Google dork query:
"""


def create_google_dork_prompt() -> PromptTemplate:
    """创建 Google Dork Generator prompt"""
    return PromptTemplate(
        template=GOOGLE_DORK_TEMPLATE,
        input_variables=["description", "constraints"]
    )

