from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://agent:agent@db:5432/agent"
    anthropic_api_key: str
    resend_api_key: str = ""
    from_email: str = "briefings@example.com"

    # Model tiers — §3.5 of architecture doc.
    # Haiku for high-volume per-item work; Sonnet/Opus for final synthesis.
    workhorse_model: str = "claude-haiku-4-5-20251001"
    premium_model: str = "claude-sonnet-4-6"

    sources_yaml_path: str = "sources.yaml"
    llm_log_path: str = "llm_logs/calls.jsonl"


settings = Settings()
