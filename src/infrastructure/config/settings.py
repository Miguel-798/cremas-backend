"""
Settings - Infrastructure Layer

Configuración de la aplicación usando Pydantic Settings + config.yaml.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config() -> dict:
    """Load configuration from config.yaml file."""
    # Path is relative to the project root (where main.py is)
    config_path = Path.cwd() / "config.yaml"
    
    if not config_path.exists():
        # Use basic logging since settings isn't configured yet
        import logging
        logging.warning(f"config.yaml not found at {config_path}")
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Replace ${ENV_VAR} placeholders with actual env var values
    def replace_env_vars(obj):
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
        elif isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        return obj
    
    return replace_env_vars(config) if config else {}


class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    
    Carga variables de entorno desde .env automáticamente.
    Carga configuración desde config.yaml.
    """
    
    # Database
    database_url: str = Field(
        default="",
        description="URL de conexión a PostgreSQL (asyncpg)"
    )
    database_pool_size: int = Field(default=10, description="DB connection pool size")
    database_max_overflow: int = Field(default=20, description="DB max overflow connections")
    database_pool_timeout: int = Field(default=30, description="DB pool timeout (seconds)")
    database_pool_recycle: int = Field(default=1800, description="DB pool recycle (seconds)")
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Supabase
    supabase_url: str = Field(default="", description="URL de Supabase")
    supabase_anon_key: str = Field(default="", description="Anon key de Supabase")
    supabase_service_role_key: str = Field(default="", description="Service role key de Supabase")
    
    # JWKS Cache (Auth Security)
    jwks_cache_ttl: int = Field(default=3600, description="JWKS cache TTL in seconds")
    jwks_fetch_timeout: int = Field(default=10, description="JWKS fetch timeout in seconds")
    
    # Environment
    env: str = Field(default="development", description="Environment: development | production")
    
    # CORS - carga del config.yaml
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # Gmail API
    gmail_client_id: str = Field(default="", description="Client ID de Google Cloud")
    gmail_client_secret: str = Field(default="", description="Client Secret de Google Cloud")
    gmail_refresh_token: str = Field(default="", description="Refresh token de Gmail")
    gmail_from_email: str = Field(default="", description="Email remitente")
    gmail_to_email: str = Field(default="", description="Email destinatario")
    
    # App
    app_name: str = Field(default="Cremas Inventory", description="Nombre de la app")
    app_version: str = Field(default="1.0.0", description="Versión de la app")
    debug: bool = Field(default=True, description="Modo debug")
    
    # Business Rules
    low_stock_threshold: int = Field(default=3, description="Umbral de stock bajo")
    reservation_expiry_days: int = Field(default=2, description="Días de expiry de reservas")
    
    # Cache
    cache_enabled: bool = Field(default=False, description="Enable in-memory query result caching")
    cache_default_ttl: int = Field(default=60, description="Default cache TTL in seconds")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def load_allowed_origins_from_yaml(cls, v):
        """Load allowed_origins from config.yaml if not provided via env var."""
        if v and v != ["http://localhost:3000"]:
            return v
        
        yaml_config = load_yaml_config()
        if yaml_config and "app" in yaml_config:
            origins = yaml_config["app"].get("allowed_origins", [])
            if origins:
                return origins
        
        return v
    
    @field_validator("app_name", mode="before")
    @classmethod
    def load_app_name_from_yaml(cls, v):
        """Load app_name from config.yaml if not provided via env var."""
        if v and v != "Cremas Inventory":
            return v
        
        yaml_config = load_yaml_config()
        if yaml_config and "app" in yaml_config:
            name = yaml_config["app"].get("name")
            if name:
                return name
        
        return v
    
    @field_validator("debug", mode="before")
    @classmethod
    def load_debug_from_yaml(cls, v):
        """Load debug from config.yaml if not provided via env var."""
        if v is not True:
            return v
        
        yaml_config = load_yaml_config()
        if yaml_config and "app" in yaml_config:
            debug = yaml_config["app"].get("debug")
            if debug is not None:
                return debug
        
        return v
    
    @field_validator("database_pool_size", mode="before")
    @classmethod
    def load_database_pool_size_from_yaml(cls, v):
        """Load database pool_size from config.yaml if not provided via env var."""
        if v != 10:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "database" in yaml_config:
            val = yaml_config["database"].get("pool_size")
            if val is not None:
                return val
        return v
    
    @field_validator("database_max_overflow", mode="before")
    @classmethod
    def load_database_max_overflow_from_yaml(cls, v):
        """Load database max_overflow from config.yaml if not provided via env var."""
        if v != 20:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "database" in yaml_config:
            val = yaml_config["database"].get("max_overflow")
            if val is not None:
                return val
        return v
    
    @field_validator("database_pool_timeout", mode="before")
    @classmethod
    def load_database_pool_timeout_from_yaml(cls, v):
        """Load database pool_timeout from config.yaml if not provided via env var."""
        if v != 30:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "database" in yaml_config:
            val = yaml_config["database"].get("pool_timeout")
            if val is not None:
                return val
        return v
    
    @field_validator("database_pool_recycle", mode="before")
    @classmethod
    def load_database_pool_recycle_from_yaml(cls, v):
        """Load database pool_recycle from config.yaml if not provided via env var."""
        if v != 1800:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "database" in yaml_config:
            val = yaml_config["database"].get("pool_recycle")
            if val is not None:
                return val
        return v
    
    @field_validator("database_echo", mode="before")
    @classmethod
    def load_database_echo_from_yaml(cls, v):
        """Load database echo from config.yaml if not provided via env var."""
        if v is not False:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "database" in yaml_config:
            val = yaml_config["database"].get("echo")
            if val is not None:
                return val
        return v
    
    @field_validator("cache_enabled", mode="before")
    @classmethod
    def load_cache_enabled_from_yaml(cls, v):
        """Load cache_enabled from config.yaml if not provided via env var."""
        if v is not False:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "cache" in yaml_config:
            val = yaml_config["cache"].get("enabled")
            if val is not None:
                return val
        return v
    
    @field_validator("cache_default_ttl", mode="before")
    @classmethod
    def load_cache_default_ttl_from_yaml(cls, v):
        """Load cache_default_ttl from config.yaml if not provided via env var."""
        if v != 60:
            return v
        yaml_config = load_yaml_config()
        if yaml_config and "cache" in yaml_config:
            val = yaml_config["cache"].get("default_ttl")
            if val is not None:
                return val
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Obtener instancia singleton de configuración.
    
    Usa lru_cache para evitar recargar Settings en cada request.
    """
    return Settings()


# Instancia global de settings
settings = get_settings()
