"""
Reddit Provider Factory
根据配置选择使用 Apify 或 RapidAPI
"""
import logging
from typing import Union

from app.core.config import settings
from app.providers.reddit.apify import ApifyRedditProvider
from app.providers.reddit.rapidapi import RapidAPIRedditProvider


logger = logging.getLogger(__name__)


# Type alias for Reddit providers
RedditProvider = Union[ApifyRedditProvider, RapidAPIRedditProvider]


def get_reddit_provider() -> RedditProvider:
    """
    根据配置返回对应的 Reddit Provider

    配置项: REDDIT_API_PROVIDER
    - "official" 或 "apify": 使用 Apify (默认)
    - "rapidapi": 使用 RapidAPI

    Returns:
        ApifyRedditProvider 或 RapidAPIRedditProvider 实例
    """
    provider_type = settings.reddit_api_provider.lower()

    if provider_type == "rapidapi":
        logger.info("Using RapidAPI Reddit Provider")
        return RapidAPIRedditProvider()
    else:
        # 默认使用 Apify (包括 "official" 和 "apify")
        logger.info("Using Apify Reddit Provider")
        return ApifyRedditProvider()
