from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource
from pydantic_settings.sources.base import InitSettingsSource


class Settings(BaseSettings):
    app_name: str = "flight-gateway-api"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_gateway"
    redis_url: str = "redis://localhost:6379/0"
    mock_travel_api_url: str = "https://mock-travel-api.vercel.app"
    legacy_api_timeout_seconds: float = 10.0
    legacy_api_retry_count: int = 2
    legacy_api_backoff_seconds: float = 0.25
    flight_search_cache_ttl_seconds: int = 300
    booking_cache_ttl_seconds: int = 300
    auth_header_name: str = "X-API-Token"
    auth_token: str = "change-me"

    model_config = SettingsConfigDict(
        yaml_file="env.yaml",
        yaml_file_encoding="utf-8",
        yaml_config_section="flight_gateway",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        try:
            yaml_source = YamlConfigSettingsSource(settings_cls)
        except (FileNotFoundError, KeyError):
            yaml_source = SafeYamlConfigSettingsSource(settings_cls)
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            yaml_source,
        )


class SafeYamlConfigSettingsSource(YamlConfigSettingsSource):
    def __init__(self, settings_cls) -> None:
        self.yaml_file_path = settings_cls.model_config.get("yaml_file")
        self.yaml_file_encoding = settings_cls.model_config.get("yaml_file_encoding")
        self.yaml_config_section = settings_cls.model_config.get("yaml_config_section")
        self.yaml_data = {}
        InitSettingsSource.__init__(self, settings_cls, {})


@lru_cache
def get_settings() -> Settings:
    return Settings()
