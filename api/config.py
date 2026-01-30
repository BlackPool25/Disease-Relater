"""
Configuration module for Disease-Relater API.

Provides Pydantic-based settings management with environment variable validation.
All sensitive configuration is loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import List, Optional, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration values are validated on startup. Sensitive values
    must be provided via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(
        default="Disease-Relater API", description="API application name"
    )
    app_version: str = Field(default="1.0.0", description="API version")
    debug: bool = Field(default=False, description="Debug mode flag")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=5000, description="Server port")

    # Supabase settings - support both direct URL or project ref construction
    supabase_url: Optional[str] = Field(
        default=None, description="Supabase project URL"
    )
    supabase_key: Optional[str] = Field(
        default=None, description="Supabase API key (service role or anon)"
    )
    supabase_service_key: Optional[str] = Field(
        default=None, description="Supabase service role key (alias for supabase_key)"
    )
    supabase_project_ref: Optional[str] = Field(
        default=None, description="Supabase project reference (for URL construction)"
    )
    supabase_db_url: Optional[str] = Field(
        default=None, description="Direct PostgreSQL connection URL"
    )

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"], description="Allowed HTTP methods"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"], description="Allowed HTTP headers"
    )

    # Security settings
    api_rate_limit: int = Field(default=100, description="API rate limit per minute")
    max_request_size: int = Field(
        default=1048576, description="Max request size in bytes (1MB)"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port number is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url_format(cls, v):
        """Validate Supabase URL format if provided."""
        if v is not None and not v.startswith("https://"):
            raise ValueError("Supabase URL must start with https://")
        return v

    @model_validator(mode="after")
    def validate_supabase_config(self) -> Self:
        """Validate and construct Supabase configuration after all fields are set.

        This validator:
        1. Constructs SUPABASE_URL from SUPABASE_PROJECT_REF if URL not provided
        2. Uses SUPABASE_SERVICE_KEY as fallback for SUPABASE_KEY
        """
        # Handle URL construction from project ref
        if self.supabase_url is None:
            if self.supabase_project_ref:
                self.supabase_url = f"https://{self.supabase_project_ref}.supabase.co"
            else:
                raise ValueError(
                    "Either SUPABASE_URL or SUPABASE_PROJECT_REF must be provided"
                )

        # Handle key alias - use SUPABASE_SERVICE_KEY if SUPABASE_KEY not set
        if self.supabase_key is None:
            if self.supabase_service_key:
                self.supabase_key = self.supabase_service_key
            else:
                raise ValueError(
                    "Either SUPABASE_KEY or SUPABASE_SERVICE_KEY must be provided"
                )

        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses LRU cache to avoid reloading settings on every request.
    Settings are loaded once at startup.

    Returns:
        Settings: Application settings instance

    Example:
        >>> from api.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.app_name)
        'Disease-Relater API'
    """
    return Settings()


# Convenience function for direct access
def get_setting(name: str, default=None):
    """Get a specific setting value by name.

    Args:
        name: Setting attribute name
        default: Default value if setting not found

    Returns:
        Setting value or default

    Example:
        >>> from api.config import get_setting
        >>> port = get_setting("port", 5000)
    """
    settings = get_settings()
    return getattr(settings, name, default)


if __name__ == "__main__":
    # Test settings loading
    settings = get_settings()
    print(f"App Name: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Host: {settings.host}:{settings.port}")
    print(f"CORS Origins: {settings.cors_origins}")
    url_display = (
        settings.supabase_url[:30] + "..."
        if settings.supabase_url
        else "Not configured"
    )
    print(f"Supabase URL: {url_display}")
