import logging
import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


class ApifyClient:
    def __init__(self):
        self.token = settings.apify_token
        self.base_url = "https://api.apify.com/v2"

    def run_actor(self, actor_id: str, run_input: dict) -> list[dict]:
        logger.info("Apify actor run started: %s with input: %s", actor_id, run_input)
        try:
            result = requests.post(
                f"{self.base_url}/acts/{actor_id}/run-sync-get-dataset-items",
                params={"token": self.token, "clean": "true"},
                json=run_input,
                timeout=120,
            )
            result.raise_for_status()
            items = result.json()
            logger.info("Apify actor run completed: %s (%s items)", actor_id, len(items))
            return items
        except requests.exceptions.HTTPError as e:
            logger.error("Apify actor HTTP error: %s - Response: %s", e, result.text if result else "No response")
            raise
        except requests.exceptions.Timeout:
            logger.error("Apify actor timeout after 120s: %s", actor_id)
            raise
        except Exception as e:
            logger.error("Apify actor unexpected error: %s", e, exc_info=True)
            raise
