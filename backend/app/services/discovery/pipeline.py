from dataclasses import dataclass
import logging
from typing import Optional

from app.core.config import settings
from app.providers.base import GoogleSearchProvider, InstagramScrapeProvider
from app.providers.google.search import ApifyGoogleSearchProvider
from app.providers.instagram.scrape import ApifyInstagramProvider
from app.services.llm.intent import IntentParser
from app.services.llm.dork import GoogleDorkGenerator
from app.services.llm.profile_summary import ProfileSummaryGenerator
from app.services.llm.profile_attributes import ProfileAttributeExtractor
from app.services.llm.audience_analysis import AudienceAnalyzer
from app.services.llm.collaboration_analysis import CollaborationAnalyzer
from app.services.llm.embeddings import EmbeddingService
from app.services.vector.pinecone import PineconeVectorStore


logger = logging.getLogger(__name__)


@dataclass
class DiscoveryCandidate:
    handle: str
    name: str
    bio: str
    profile_summary: str
    profile_url: str
    
    # Basic metrics
    followers: float
    avg_likes: float
    avg_comments: float
    avg_video_views: float
    
    # Peak performance metrics
    highest_likes: float
    highest_comments: float
    highest_video_views: float
    
    # Post analysis metrics
    post_sharing_percentage: float
    post_collaboration_percentage: float
    
    # Advanced analysis
    audience_analysis: str
    collaboration_opportunity: str
    
    # Contact and metadata
    email: str
    external_url: str
    category: str
    tags: str
    country: str
    gender: str


class DiscoveryPipeline:
    def __init__(
        self,
        search_provider: Optional[GoogleSearchProvider] = None,
        instagram_provider: Optional[InstagramScrapeProvider] = None,
    ):
        self.search_provider = search_provider or ApifyGoogleSearchProvider()
        self.instagram_provider = instagram_provider or ApifyInstagramProvider()
        self.embedding_service = EmbeddingService()
        self.vector_store = PineconeVectorStore()
        
        # 根据配置选择 LangChain 或传统实现
        if settings.use_langchain_chains:
            from app.services.langchain.chains.intent_chain import IntentChainService
            from app.services.langchain.chains.dork_chain import GoogleDorkChainService
            from app.services.langchain.chains.profile_chain import ProfileSummaryChainService
            from app.services.langchain.chains.audience_chain import AudienceAnalysisChainService
            from app.services.langchain.chains.collaboration_chain import CollaborationAnalysisChainService
            
            self.intent_parser = IntentChainService()
            self.dork_generator = GoogleDorkChainService()
            self.profile_summarizer = ProfileSummaryChainService()
            self.audience_analyzer = AudienceAnalysisChainService()
            self.collaboration_analyzer = CollaborationAnalysisChainService()
            logger.info("Using LangChain chains for all LLM services")
        else:
            self.intent_parser = IntentParser()
            self.dork_generator = GoogleDorkGenerator()
            self.profile_summarizer = ProfileSummaryGenerator()
            self.audience_analyzer = AudienceAnalyzer()
            self.collaboration_analyzer = CollaborationAnalyzer()
            logger.info("Using legacy LLM services")
        
        self.profile_attribute_extractor = ProfileAttributeExtractor()

    def run(self, description: str, constraints: str) -> list[DiscoveryCandidate]:
        query = self.dork_generator.generate(description, constraints)
        if not query:
            intent = self.intent_parser.parse(description, constraints)
            query = f"site:instagram.com/*/ {intent}"
        logger.info("Discovery query: %s", query)
        search_results = self.search_provider.search(query, settings.max_candidates)

        handles = self._extract_handles(search_results)
        logger.info("Extracted %s handles from search results", len(handles))
        candidates = []
        for handle in handles:
            # Fetch profile with latestPosts in one API call
            profile = self.instagram_provider.profile(handle)
            if not profile:
                continue
            
            # Extract recent posts from profile data (more efficient than separate API call)
            posts = profile.get("latestPosts", [])[:6]
            
            # If no latestPosts in profile, fall back to separate posts call
            if not posts:
                logger.info("No latestPosts in profile for %s, fetching separately", handle)
                posts = self.instagram_provider.recent_posts(handle, 6)
            
            candidate = self._normalize(handle, profile, posts)
            candidates.append(candidate)

        self._upsert_vectors(candidates)
        logger.info("Discovery upserted %s candidates", len(candidates))
        return candidates

    def _extract_handles(self, search_results: list[dict]) -> list[str]:
        handles = []
        for item in search_results:
            url = item.get("url", "") or item.get("link", "")
            if "instagram.com" not in url:
                continue
            parts = url.split("instagram.com/")[-1].split("/")
            handle = parts[0].strip("@").strip()
            if handle and handle not in handles:
                handles.append(handle)
        return handles

    def _normalize(self, handle: str, profile: dict, posts: list[dict]) -> DiscoveryCandidate:
        """
        Normalize Instagram profile and posts data into a DiscoveryCandidate.
        Performs comprehensive analysis including metrics calculation and LLM-based insights.
        """
        # Basic profile data
        followers = float(profile.get("followersCount", 0))
        bio = profile.get("biography", "")
        category = profile.get("businessCategoryName", "")
        tags = ",".join(profile.get("hashtags", [])) if profile.get("hashtags") else ""
        name = profile.get("fullName", "")
        profile_url = f"https://instagram.com/{handle}"
        
        # Contact information
        email = profile.get("publicEmail", "") or profile.get("email", "")
        external_url = profile.get("externalUrl", "") or profile.get("external_url", "")
        
        # Calculate engagement metrics from posts
        likes = [post.get("likesCount", 0) for post in posts if post]
        comments = [post.get("commentsCount", 0) for post in posts if post]
        video_views = [post.get("videoViewCount", 0) for post in posts if post and post.get("videoViewCount")]
        
        avg_likes = sum(likes) / len(likes) if likes else 0.0
        avg_comments = sum(comments) / len(comments) if comments else 0.0
        avg_video_views = sum(video_views) / len(video_views) if video_views else 0.0
        
        highest_likes = max(likes) if likes else 0.0
        highest_comments = max(comments) if comments else 0.0
        highest_video_views = max(video_views) if video_views else 0.0
        
        # Calculate post analysis metrics
        sharing_posts = 0
        collaboration_posts = 0
        
        for post in posts:
            if not post:
                continue
            caption = post.get("caption", "").lower()
            
            # Detect sharing behavior (resharing others' content)
            if any(keyword in caption for keyword in ["repost", "regram", "via @", "📸:", "credit:"]):
                sharing_posts += 1
            
            # Detect collaboration (sponsored, partnerships, brand mentions)
            mentions = post.get("mentions", [])
            if mentions or any(keyword in caption for keyword in ["#ad", "#sponsored", "#partner", "collaboration", "collab"]):
                collaboration_posts += 1
        
        total_posts = len(posts) if posts else 1  # Avoid division by zero
        post_sharing_percentage = (sharing_posts / total_posts) * 100
        post_collaboration_percentage = (collaboration_posts / total_posts) * 100
        
        # LLM-based analysis
        summary = self.profile_summarizer.generate(profile, posts)
        attributes = self.profile_attribute_extractor.extract(profile, posts)
        
        # Advanced audience and collaboration analysis
        audience_analysis = self.audience_analyzer.analyze(profile, posts)
        collaboration_opportunity = self.collaboration_analyzer.analyze(profile, posts)
        
        logger.info(
            "Normalized profile %s: followers=%s, avg_likes=%.1f, avg_comments=%.1f, "
            "sharing=%.1f%%, collab=%.1f%%",
            handle, followers, avg_likes, avg_comments,
            post_sharing_percentage, post_collaboration_percentage
        )
        
        return DiscoveryCandidate(
            handle=handle,
            name=name,
            bio=bio,
            profile_summary=summary,
            profile_url=profile_url,
            followers=followers,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            avg_video_views=avg_video_views,
            highest_likes=highest_likes,
            highest_comments=highest_comments,
            highest_video_views=highest_video_views,
            post_sharing_percentage=post_sharing_percentage,
            post_collaboration_percentage=post_collaboration_percentage,
            audience_analysis=audience_analysis,
            collaboration_opportunity=collaboration_opportunity,
            email=email,
            external_url=external_url,
            category=category,
            tags=tags,
            country=attributes.get("country", ""),
            gender=attributes.get("gender", ""),
        )

    def _upsert_vectors(self, candidates: list[DiscoveryCandidate]) -> None:
        if not candidates:
            return
        # Improved embedding text with more structure and context
        texts = [
            (
                f"Instagram creator @{c.handle} ({c.name}) from {c.country}. "
                f"Category: {c.category}. Followers: {int(c.followers):,}. "
                f"Bio: {c.bio} "
                f"Profile: {c.profile_summary} "
                f"Tags: {c.tags} "
                f"Audience: {c.audience_analysis} "
                f"Collaboration: {c.collaboration_opportunity}"
            )
            for c in candidates
        ]
        if settings.embedding_provider.lower() == "pinecone":
            if not self.vector_store.supports_text_records():
                raise RuntimeError(
                    "Pinecone index-integrated embedding requires the newer pinecone SDK "
                    "with upsert_records/search support. Upgrade pinecone or set EMBEDDING_PROVIDER=openai."
                )
            records = []
            for candidate, text in zip(candidates, texts):
                # Pinecone requires metadata values to be string, number, boolean, or list of strings
                # Ensure all values are properly typed and not None
                metadata = {}
                
                # String fields - ensure they are strings, not None
                string_fields = [
                    "handle", "name", "bio", "profile_summary", "category", "tags", 
                    "profile_url", "country", "gender", "email", "external_url",
                    "audience_analysis", "collaboration_opportunity"
                ]
                for key in string_fields:
                    value = getattr(candidate, key, "")
                    if value is None:
                        metadata[key] = ""
                    elif isinstance(value, str):
                        metadata[key] = value
                    else:
                        metadata[key] = str(value)
                
                # Set platform explicitly
                metadata["platform"] = "instagram"
                
                # Numeric fields - ensure they are floats, not None
                numeric_fields = {
                    "followers": candidate.followers,
                    "avg_likes": candidate.avg_likes,
                    "avg_comments": candidate.avg_comments,
                    "avg_video_views": candidate.avg_video_views,
                    "highest_likes": candidate.highest_likes,
                    "highest_comments": candidate.highest_comments,
                    "highest_video_views": candidate.highest_video_views,
                    "post_sharing_percentage": candidate.post_sharing_percentage,
                    "post_collaboration_percentage": candidate.post_collaboration_percentage,
                }
                for key, value in numeric_fields.items():
                    metadata[key] = float(value) if value is not None else 0.0
                
                records.append(
                    {
                        "id": str(candidate.handle),
                        "text": str(text),
                        "metadata": metadata,
                    }
                )
            self.vector_store.upsert_texts(records)
            return

        embeddings = self.embedding_service.embed_documents(texts)
        vectors = []
        for candidate, embedding in zip(candidates, embeddings):
            vectors.append(
                {
                    "id": candidate.handle,
                    "values": embedding,
                    "metadata": {
                        "handle": candidate.handle,
                        "name": candidate.name,
                        "bio": candidate.bio,
                        "profile_summary": candidate.profile_summary,
                        "category": candidate.category,
                        "tags": candidate.tags,
                        "followers": candidate.followers,
                        "avg_likes": candidate.avg_likes,
                        "avg_comments": candidate.avg_comments,
                        "avg_video_views": candidate.avg_video_views,
                        "highest_likes": candidate.highest_likes,
                        "highest_comments": candidate.highest_comments,
                        "highest_video_views": candidate.highest_video_views,
                        "post_sharing_percentage": candidate.post_sharing_percentage,
                        "post_collaboration_percentage": candidate.post_collaboration_percentage,
                        "audience_analysis": candidate.audience_analysis,
                        "collaboration_opportunity": candidate.collaboration_opportunity,
                        "email": candidate.email,
                        "external_url": candidate.external_url,
                        "profile_url": candidate.profile_url,
                        "country": candidate.country,
                        "gender": candidate.gender,
                        "platform": "instagram",
                    },
                }
            )
        self.vector_store.upsert(vectors)
