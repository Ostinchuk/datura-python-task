import logging
from typing import Any, Optional
import httpx
from app.core.settings import settings

logger = logging.getLogger(__name__)


class TwitterService:
    """Service for interacting with Twitter data via Datura.ai API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.DATURA_API_KEY.get_secret_value()
        self.base_url = "https://apis.datura.ai/twitter"

    async def search_tweets(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """
        Search for recent tweets using Datura.ai API.
        """
        logger.info(f"Searching Twitter for: '{query}' (limit: {limit})")

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "query": query,
            "count": limit,
            "sort": "Top",
            "is_image": False,
            "is_quote": False,
            "is_video": False,
            "lang": "en",
            "min_likes": 0,
            "min_replies": 0,
            "min_retweets": 0,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url, headers=headers, json=payload
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"Retrieved {len(data)} tweets")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from Datura API: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Datura API HTTP error: {e.response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"Request error when calling Datura API: {str(e)}")
            raise RuntimeError(f"Datura API request error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error when searching tweets: {str(e)}")
            raise RuntimeError(f"Twitter search failed: {str(e)}")

    async def search_subnet_tweets(
        self, netuid: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search for tweets about a specific Bittensor subnet.
        """
        query = f"Bittensor netuid {netuid}"
        return await self.search_tweets(query, limit)

    def extract_tweet_text(self, tweets: list[dict[str, Any]]) -> list[str]:
        """
        Extract just the text content from tweet objects.
        """
        return [tweet.get("text", "") for tweet in tweets if tweet.get("text")]
