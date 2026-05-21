import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Providers & Models
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
    DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Orchestration configuration
    MAX_STEPS: int = 5
    SEARCH_LIMIT: int = 5
    TIMEOUT_SECONDS: int = 15
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0

    # Project directory
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
