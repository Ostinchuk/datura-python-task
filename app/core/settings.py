from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_TOKEN: SecretStr = Field(
        ...,
        description="Authentication token for API access",
    )
    DATURA_API_KEY: SecretStr = Field(
        ...,
        description="API key for Datura.ai services",
    )
    CHUTES_API_KEY: SecretStr = Field(
        ...,
        description="API key for Chutes.ai services",
    )
    CACHE_SERVER_URL: str = Field(
        ...,
        description="Redis connection URL for caching",
    )
    BLOCKCHAIN_SERVICE_URL: str = Field(
        ...,
        description="WebSocket endpoint for Bittensor blockchain",
    )
    UVICORN_RELOAD: bool = Field(
        default=False,
        description="Enable auto-reload for Uvicorn server",
    )

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
