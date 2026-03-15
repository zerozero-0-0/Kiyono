"""Application configuration using typed settings.

This module centralizes environment-driven settings for the project.
Values are loaded from `.env` (if present) and can be overridden by
real environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Attributes:
        app_env: Runtime environment name.
        log_level: Log verbosity level.
        host: Host address for the API server.
        port: Port for the API server.
        llm_provider: Active LLM provider identifier.
        llm_model: Model name used by the selected provider.
        gemini_api_key: API key for Gemini.
        openai_api_key: API key for OpenAI.
        anthropic_api_key: API key for Anthropic.
        request_timeout_seconds: Timeout for outbound LLM requests.
        max_titles: Upper bound for generated title count.
        default_titles: Default title count when not specified.
        temperature: Generation temperature.
        max_output_tokens: Max tokens for model output.
    """

    model_config = SettingsConfigDict(  # pyright: ignore[reportUnannotatedClassAttribute]
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    llm_model: str = "gemini-2.5-flash"

    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    request_timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_titles: int = Field(default=10, ge=1, le=20)
    default_titles: int = Field(default=8, ge=1, le=20)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=8000, ge=64, le=8192)

    @property
    def provider_api_key(self) -> SecretStr | None:
        """Return API key for the currently selected provider."""
        if self.llm_provider == "gemini":
            return self.gemini_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None

    @property
    def provider_api_key_value(self) -> str | None:
        """Return plain API key string for the selected provider.

        Returns:
            API key as plain string, or `None` when not configured.
        """
        key = self.provider_api_key
        return key.get_secret_value() if key is not None else None

    def validate_runtime_constraints(self) -> None:
        """Validate cross-field runtime constraints.

        Raises:
            ValueError: If settings combination is invalid.
        """
        if self.default_titles > self.max_titles:
            raise ValueError("default_titles must be less than or equal to max_titles.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance.

    Returns:
        Singleton-like cached `Settings` object.
    """
    settings = Settings()
    settings.validate_runtime_constraints()
    return settings
