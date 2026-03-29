from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "LLM Cost + Latency Monitor"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    default_feature: str = "chat"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
