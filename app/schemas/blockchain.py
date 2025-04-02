from typing import Union

from pydantic import BaseModel, Field


class TaoDividendResponse(BaseModel):
    results: dict[str, dict[str, int]] = Field(
        ..., description="Dividend results by subnet and hotkey"
    )
    netuid: Union[int, str] = Field(
        ..., description="The netuid that was queried, or 'all'"
    )
    hotkey: Union[str, str] = Field(
        ..., description="The hotkey that was queried, or 'all'"
    )
    cached: bool = Field(False, description="Whether this result came from cache")
