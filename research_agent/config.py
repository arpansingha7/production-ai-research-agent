import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Primary provider: groq is much faster and has no free-tier rate limits
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"
    # Upgraded to 70b for much better reasoning quality at Groq's fast inference speeds
    DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Orchestration configuration
    MAX_STEPS: int = 4          # Reduced from 5 — 4 steps = same quality, fewer LLM calls
    SEARCH_LIMIT: int = 5
    TIMEOUT_SECONDS: int = 8    # Reduced from 15 — fail faster on hung scrapers
    MAX_RETRIES: int = 2        # Reduced from 3 — fail fast, let fallback take over
    BACKOFF_FACTOR: float = 1.5

    # Wall-clock timeout: force synthesis if total elapsed > this many seconds
    QUERY_TIMEOUT_SECONDS: int = 60

    # Max words per scraped page — keep prompts lean
    MAX_SCRAPE_WORDS: int = 1500  # Reduced from 3000

    # History snippet cap per step in _decide_next_step
    MAX_HISTORY_SNIPPET_CHARS: int = 800  # Reduced from 3000

    # Project directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
