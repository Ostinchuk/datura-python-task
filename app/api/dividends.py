from typing import Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from app.core.settings import settings
from app.schemas.blockchain import TaoDividendResponse
from app.services.blockchain import BlockchainService
from app.services.cache import CacheService

router = APIRouter(prefix="/api/v1", tags=["blockchain"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = logging.getLogger("dividends_api")

blockchain_service = BlockchainService(network_endpoint=settings.BLOCKCHAIN_SERVICE_URL)
cache_service = CacheService(url=settings.CACHE_SERVER_URL)


async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """Verify the authentication token."""
    if token != settings.API_TOKEN.get_secret_value():
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.get("/tao_dividends", response_model=TaoDividendResponse)
async def get_tao_dividends(
    netuid: Optional[int] = Query(None, description="Subnet ID to query"),
    hotkey: Optional[str] = Query(None, description="Account address to query"),
    trade: bool = Query(
        False, description="Trigger trading based on sentiment analysis"
    ),
    token: str = Depends(verify_token),
) -> TaoDividendResponse:
    """
    Get Tao dividends for a subnet and/or hotkey.

    - If netuid is omitted, returns data for all subnets
    - If hotkey is omitted, returns data for all hotkeys in the specified subnet(s)
    - If trade=true, triggers a background task to analyze sentiment and stake/unstake
    """
    try:
        cache_key = f"dividends:{netuid or 'all'}:{hotkey or 'all'}"

        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return TaoDividendResponse(**cached_result)

        result = await blockchain_service.query_tao_dividends(
            netuid=netuid, hotkey=hotkey
        )

        data_to_cache = result.model_dump()
        data_to_cache["cached"] = True

        await cache_service.set(
            key=cache_key,
            value=data_to_cache,
            ttl=120,
        )

        # TODO: Implement sentiment analysis and trading logic
        if trade:
            # analyze_sentiment_and_trade is a Celery task
            logger.info(
                f"Triggering sentiment analysis and trading for netuid {netuid}, hotkey {hotkey}"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying blockchain data: {str(e)}"
        )
