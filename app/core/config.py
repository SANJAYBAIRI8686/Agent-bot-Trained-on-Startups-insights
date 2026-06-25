import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "nvidia"  # "nvidia" or "openai"
    OPENAI_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    LLM_MODEL: str = "meta/llama-3.1-70b-instruct"

    # Search Tool Settings
    TAVILY_API_KEY: Optional[str] = None
    DOCX_DIR: str = "."

    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set if LLM_PROVIDER is 'openai'")
        if self.LLM_PROVIDER == "nvidia" and not self.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY must be set if LLM_PROVIDER is 'nvidia'")
        return self


# Create singleton settings instance
settings = Settings()
