import asyncio
import logging
from typing import Any, Optional

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.settings import SS58_FORMAT

from app.schemas.blockchain import TaoDividendResponse

logger = logging.getLogger("blockchain_service")


class BlockchainService:
    """Service for interacting with the Bittensor blockchain."""

    def __init__(
        self,
        network_endpoint: str = "wss://entrypoint-finney.opentensor.ai:443",
        num_subnets: int = 20,
    ) -> None:
        """Initialize the blockchain service with the specified endpoint."""
        self.network_endpoint = network_endpoint
        self.num_subnets = num_subnets
        self.ss58_format = SS58_FORMAT

    async def query_tao_dividends(
        self, netuid: Optional[int] = None, hotkey: Optional[str] = None
    ) -> TaoDividendResponse:
        """Query Tao dividends from the Bittensor blockchain asynchronously."""
        async with AsyncSubstrateInterface(
            self.network_endpoint, ss58_format=self.ss58_format
        ) as substrate:
            try:
                block_hash = await substrate.get_chain_head()

                results: dict[str, dict[str, Any]] = {}

                netuids_to_query = (
                    [netuid] if netuid is not None else range(1, self.num_subnets + 1)
                )

                async def process_subnet_query(
                    net_id: int,
                ) -> tuple[int, dict[str, Any]]:
                    """Process query for a specific subnet."""
                    try:
                        query_result = await substrate.query_map(
                            "SubtensorModule",
                            "TaoDividendsPerSubnet",
                            [net_id],
                            block_hash=block_hash,
                        )

                        subnet_dividends = {}
                        async for key, value in query_result:
                            account_id = decode_account_id(key)

                            if hotkey and account_id != hotkey:
                                continue

                            subnet_dividends[account_id] = value.value

                        return net_id, subnet_dividends
                    except Exception as e:
                        logger.error(f"Error querying netuid {net_id}: {str(e)}")
                        return net_id, {}

                tasks = [process_subnet_query(net_id) for net_id in netuids_to_query]
                subnet_results = await asyncio.gather(*tasks)

                for net_id, subnet_data in subnet_results:
                    if subnet_data:
                        results[f"netuid_{net_id}"] = subnet_data

            except Exception as e:
                logger.error(f"Failed to query blockchain: {str(e)}")
                raise RuntimeError(f"Blockchain query failed: {str(e)}")

        return TaoDividendResponse(
            results=results,
            netuid=netuid if netuid is not None else "all",
            hotkey=hotkey if hotkey is not None else "all",
            cached=False,
        )

    async def stake_tao(self) -> Any:
        """Stake TAO tokens for a hotkey on a subnet."""
        pass

    async def unstake_tao(self) -> Any:
        """Unstake TAO tokens for a hotkey from a subnet."""
        pass
