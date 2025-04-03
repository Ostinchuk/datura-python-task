import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

logger = logging.getLogger("cache_service")


class CacheService:
    def __init__(
        self, url: str = "redis://localhost:6379/0", default_ttl: int = 120
    ) -> None:
        self.url = url
        self.default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> Optional[redis.Redis]:
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.url, encoding="utf-8", decode_responses=True
                )
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                self._client = None
                return None
        return self._client

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        client = await self._get_client()
        if client is None:
            return None
        try:
            cached_value = await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key '{key}': {e}")
            return None
        if cached_value is None:
            return None
        try:
            return json.loads(cached_value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for key '{key}': {e}")
            return None

    async def set(
        self, key: str, value: dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        client = await self._get_client()
        if client is None:
            return
        expire = ttl if ttl is not None else self.default_ttl
        try:
            data_str = json.dumps(value)
        except Exception as e:
            logger.error(f"Could not serialize value for key '{key}': {e}")
            return
        try:
            await client.set(key, data_str, ex=expire)
        except Exception as e:
            logger.error(f"Redis SET failed for key '{key}': {e}")

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")
