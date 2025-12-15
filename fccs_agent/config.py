"""Configuration module using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class FCCSConfig(BaseSettings):
    """FCCS configuration with environment variable validation."""

    # FCCS Connection (optional in mock mode)
    fccs_url: Optional[str] = Field(None, alias="FCCS_URL")
    fccs_username: Optional[str] = Field(None, alias="FCCS_USERNAME")
    fccs_password: Optional[str] = Field(None, alias="FCCS_PASSWORD")
    fccs_api_version: str = Field("v3", alias="FCCS_API_VERSION")
    fccs_mock_mode: bool = Field(False, alias="FCCS_MOCK_MODE")

    # Database (PostgreSQL for sessions + feedback)
    database_url: str = Field(
        "postgresql+psycopg://postgres:password@localhost:5432/fccs_agent",
        alias="DATABASE_URL"
    )

    # Gemini Model
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    model_id: str = Field("gemini-2.0-flash", alias="MODEL_ID")

    # Server
    port: int = Field(8080, alias="PORT")

    # Reinforcement Learning Configuration
    rl_enabled: bool = Field(True, alias="RL_ENABLED")
    rl_exploration_rate: float = Field(0.1, alias="RL_EXPLORATION_RATE")
    rl_learning_rate: float = Field(0.1, alias="RL_LEARNING_RATE")
    rl_discount_factor: float = Field(0.9, alias="RL_DISCOUNT_FACTOR")
    rl_min_samples: int = Field(5, alias="RL_MIN_SAMPLES")  # Minimum samples before using RL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


def load_config() -> FCCSConfig:
    """Load and validate configuration from environment variables."""
    config = FCCSConfig()

    # Validate FCCS credentials if not in mock mode
    if not config.fccs_mock_mode:
        if not all([config.fccs_url, config.fccs_username, config.fccs_password]):
            raise ValueError(
                "Missing FCCS credentials (FCCS_URL, FCCS_USERNAME, FCCS_PASSWORD) "
                "required when FCCS_MOCK_MODE is not true."
            )

    return config


# Global config instance
config = load_config()
