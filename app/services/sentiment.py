import logging
import re
from typing import Any, Optional

import httpx

from app.core.settings import settings

logger = logging.getLogger("sentiment_service")


class SentimentService:
    """Service for performing sentiment analysis on text using Chutes.ai API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.CHUTES_API_KEY.get_secret_value()
        self.base_url = "https://llm.chutes.ai/v1"

    async def analyze_sentiment(self, texts: list[str]) -> float:
        """
        Analyze sentiment of text(s) using Chutes.ai LLM.
        """
        combined_text = "\n\n---\n\n".join(texts)

        logger.info(f"Analyzing sentiment of {len(combined_text)} characters of text")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "unsloth/Llama-3.2-3B-Instruct",
            "prompt": (
                f"Analyze the sentiment of these tweets about Bittensor blockchain. "
                f"Return a single number between -100 (extremely negative) to +100 (extremely positive). "
                f"Tweets: {combined_text}"
            ),
            "stream": False,
            "max_tokens": 20,
            "temperature": 0.3,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

                raw_score = self._extract_sentiment_score(data)

                logger.info(f"Sentiment analysis completed. Score: {raw_score}")
                return raw_score

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from Chutes API: {e.response.status_code} - {e.response.text}"
            )
            raise RuntimeError(f"Chutes API HTTP error: {e.response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"Request error when calling Chutes API: {str(e)}")
            raise RuntimeError(f"Chutes API request error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during sentiment analysis: {str(e)}")
            raise RuntimeError(f"Sentiment analysis failed: {str(e)}")

    def _extract_sentiment_score(self, response_data: dict[str, Any]) -> float:
        """Extract sentiment score from Chutes.ai API response."""
        try:
            logger.info(f"Raw response: {response_data}")

            if "choices" in response_data and response_data["choices"]:
                text = response_data["choices"][0].get("text", "")

                score_match = re.search(r"-?\d+\.?\d*", text)
                if score_match:
                    score = float(score_match.group(0))
                    return max(-100.0, min(100.0, score))

            logger.warning(f"Could not find score in response: {response_data}")
            return 0.0

        except Exception as e:
            logger.error(f"Error parsing sentiment score: {str(e)}")
            return 0.0
