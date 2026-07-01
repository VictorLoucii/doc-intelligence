"""
Application configuration via pydantic-settings. All values are read from
environment variables (or a local .env file during development) — never
hardcoded. See CLAUDE.md Section 5.5 (GPU allocation) and 5.6 (no secrets).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- GPU allocation (CLAUDE.md Section 5.5) ---
    EMBEDDING_GPU_ID: int = 0
    RERANKER_GPU_ID: int = 1
    LLM_GPU_ID: int = 2

    # --- Reranker (CLAUDE.md Section 5.4) ---
    RELEVANCE_THRESHOLD: float = 0.3

    # --- API keys ---
    ANTHROPIC_API_KEY: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"


settings = Settings()
