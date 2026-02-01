"""
Reddit Subreddit Discovery Service
Step 1: Generate search queries from business description
Step 2: Find relevant subreddits using Apify
"""
import logging
import json
from typing import List, Dict, Any

from app.providers.reddit.factory import get_reddit_provider
from app.services.llm.client import get_llm_client


logger = logging.getLogger(__name__)


class RedditDiscoveryService:
    """
    Discovers relevant subreddits for a business using Apify Community Search actor
    """
    
    def __init__(self):
        self.reddit_provider = get_reddit_provider()
        self.llm_client = get_llm_client()
    
    def generate_search_queries(self, business_description: str) -> List[str]:
        """
        Use LLM to generate relevant search queries for finding subreddits
        
        Example:
            Input: "I sell project management SaaS for small teams"
            Output: ["project management", "productivity tools", "small business", "startups", "remote work"]
        """
        logger.info("Generating search queries for business")
        
        prompt = f"""You are helping a business find relevant Reddit communities (subreddits) for lead generation.

Business Description:
{business_description}

Generate 4-6 search queries that would help find relevant subreddits where this business's target customers hang out.

Requirements:
- Generate at least 4 but no more than 6 queries
- Focus on the industry, problems the business solves, and target audience
- Keep queries broad enough to find active communities
- Include both industry-specific and general terms
- Consider pain points and use cases

Return ONLY a JSON array of strings, no other text.

Example format: ["project management", "saas tools", "productivity", "small business owners"]"""

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.llm_client.chat(messages, temperature=0.3)
            
            # Extract text from response
            if isinstance(response, dict):
                text = response.get("text") or response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                text = str(response)
            
            logger.info(f"Raw LLM response: {text[:200]}...")  # Log first 200 chars for debugging
            
            # Clean up the response (handle markdown code blocks)
            text = text.strip()
            if text.startswith("```"):
                # Extract content between code blocks
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    # Remove language identifier (e.g., "json")
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
            
            # Try to find JSON array in the text
            import re
            # Look for JSON array pattern: [...]
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            # Parse JSON
            queries = json.loads(text)
            
            # Validate it's a list of strings
            if not isinstance(queries, list):
                raise ValueError("Response is not a list")
            if not all(isinstance(q, str) for q in queries):
                raise ValueError("Response contains non-string items")
            
            logger.info(f"Generated {len(queries)} search queries: {queries}")
            return queries
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response was: {text if 'text' in locals() else 'N/A'}")
            # Fallback: extract keywords from business description
            return self._extract_keywords_fallback(business_description)
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            logger.exception(e)
            return self._extract_keywords_fallback(business_description)
    
    def _extract_keywords_fallback(self, business_description: str) -> List[str]:
        """Fallback: Simple keyword extraction if LLM fails"""
        # Simple heuristic: split by common separators and take meaningful words
        words = business_description.lower().split()
        keywords = []
        
        # Common words to skip
        stop_words = {"i", "we", "our", "the", "a", "an", "for", "to", "of", "in", "on", "at", "by"}
        
        for word in words:
            word = word.strip(".,!?;:")
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)
        
        # Take first 5 unique keywords
        return list(dict.fromkeys(keywords))[:5]
    
    def discover_subreddits(self, search_queries: List[str], limit_per_query: int = 10) -> List[Dict[str, Any]]:
        """
        Search for subreddits using Apify Community Search actor
        一次性搜索所有关键词（节省API调用）
        Returns deduplicated list of subreddit metadata
        """
        logger.info(f"Discovering subreddits for {len(search_queries)} queries")
        
        if not search_queries:
            return []
        
        # 一次性搜索所有关键词（Apify API支持）
        results = self.reddit_provider.search_communities(
            search_queries=search_queries, 
            limit=limit_per_query * len(search_queries)  # 调整总数限制
        )
        
        all_subreddits = {}  # Use dict to deduplicate by name
        
        for subreddit in results:
            name = subreddit["name"]
            
            # Skip NSFW subreddits
            if subreddit.get("is_nsfw", False):
                continue
            
            # Ensure subscribers is not None
            if subreddit["subscribers"] is None:
                subreddit["subscribers"] = 0
            
            # Deduplicate: keep subreddit with highest subscriber count
            if name not in all_subreddits or subreddit["subscribers"] > all_subreddits[name].get("subscribers", 0):
                all_subreddits[name] = subreddit
        
        # Sort by subscribers (descending)
        sorted_subreddits = sorted(
            all_subreddits.values(),
            key=lambda x: x.get("subscribers", 0),
            reverse=True
        )
        
        logger.info(f"Discovered {len(sorted_subreddits)} unique subreddits (from 1 API call)")
        return sorted_subreddits
    
    def rank_subreddits(
        self, 
        subreddits: List[Dict[str, Any]], 
        business_description: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to rank and score subreddits by relevance to business
        Returns subreddits sorted by a composite score (relevance + activity)
        """
        logger.info(f"Ranking {len(subreddits)} subreddits by relevance")
        
        # Format subreddit info for LLM (limit to top 50 by subscribers)
        top_subreddits = subreddits[:50]
        subreddit_list = []
        for idx, sub in enumerate(top_subreddits, 1):
            subreddit_list.append(
                f"{idx}. r/{sub['name']} ({sub['subscribers']:,} subscribers) - {sub['description']}"
            )
        
        prompt = f"""You are helping a business find the most relevant Reddit communities for lead generation.

Business Description:
{business_description}

Subreddits Found:
{chr(10).join(subreddit_list)}

For each subreddit, rate its relevance from 0.0 to 1.0:
- 0.9-1.0 = Perfect match (target customers actively discussing relevant problems)
- 0.7-0.8 = Highly relevant (strong overlap with target audience)
- 0.4-0.6 = Somewhat relevant (potential but not ideal)
- 0.0-0.3 = Not relevant

Return ONLY a JSON object mapping subreddit names to scores (as decimals).

Example format: {{"SaaS": 0.95, "Entrepreneur": 0.85, "SmallBusiness": 0.75}}"""

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.llm_client.chat(messages, temperature=0.2)
            
            # Extract text
            if isinstance(response, dict):
                text = response.get("text") or response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                text = str(response)
            
            logger.info(f"Raw ranking response: {text[:200]}...")  # Log first 200 chars
            
            # Parse JSON (handle markdown code blocks)
            text = text.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
            
            # Try to find JSON object in the text
            import re
            # Look for JSON object pattern: {...}
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            scores = json.loads(text)
            
            # Validate it's a dict with numeric values
            if not isinstance(scores, dict):
                raise ValueError("Response is not a dictionary")
            
            logger.info(f"Successfully parsed scores for {len(scores)} subreddits")
            
            # Add relevance scores and calculate composite score
            for subreddit in subreddits:
                name = subreddit["name"]
                # Try both with and without "r/" prefix (LLM may return either format)
                relevance = scores.get(name) or scores.get(f"r/{name}") or 0.5
                
                # Normalize subscriber count (log scale to avoid huge subreddits dominating)
                import math
                subscriber_score = min(math.log10(subreddit['subscribers'] + 1) / 7.0, 1.0)  # 10M subs = 1.0
                
                # Composite score: 70% relevance, 30% activity/size
                composite_score = (relevance * 0.7) + (subscriber_score * 0.3)
                
                subreddit["relevance_score"] = round(relevance, 2)
                subreddit["composite_score"] = round(composite_score, 2)
            
            # Sort by composite score (relevance + activity)
            subreddits.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
            
            logger.info(f"Successfully ranked {len(subreddits)} subreddits")
            top_5_str = ", ".join([f"{s['name']}({s['relevance_score']})" for s in subreddits[:5]])
            logger.info(f"Top 5: {top_5_str}")
            
            return subreddits
        
        except Exception as e:
            logger.error(f"Error ranking subreddits: {e}")
            logger.exception(e)
            # Return original list without ranking, but add default scores
            for subreddit in subreddits:
                subreddit["relevance_score"] = 0.5
                subreddit["composite_score"] = 0.5
            return subreddits

