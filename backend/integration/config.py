import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    """Application configuration settings."""

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # Database
    DB_PATH: str = os.getenv("DB_PATH", "sessions.db")

    # CORS
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    )

    # LLM Settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    # Browser Execution Limits
    MAX_STEPS_DEFAULT: int = int(os.getenv("MAX_STEPS_DEFAULT", "5"))
    BROWSER_TIMEOUT_MS: int = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))


settings = Settings()
