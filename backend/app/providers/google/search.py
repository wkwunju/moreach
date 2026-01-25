from typing import Optional

import logging

from app.core.config import settings
from app.providers.apify.client import ApifyClient
from app.providers.base import GoogleSearchProvider


logger = logging.getLogger(__name__)


class ApifyGoogleSearchProvider(GoogleSearchProvider):
    def __init__(self, client: Optional[ApifyClient] = None):
        self.client = client or ApifyClient()

    def search(self, query: str, limit: int) -> list[dict]:
        run_input = {
            "queries": query,
            "resultsPerPage": min(limit, 10),
            "maxPagesPerQuery": 1,
        }
        items = self.client.run_actor(settings.apify_google_actor, run_input)
        logger.info("Apify Google raw items: %s", len(items))
        organic = []
        for item in items:
            if "organicResults" not in item:
                logger.info("Apify Google item keys: %s", list(item.keys()))
            results = item.get("organicResults", [])
            if results:
                organic.extend(results)
            else:
                organic.append(item)
        logger.info("Apify Google organic results: %s", len(organic))
        return organic[:limit]
