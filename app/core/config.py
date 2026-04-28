from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "llm-free-conector"
    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_free_connector"
    connector_api_key: str = ""

    newapi_base_url: AnyHttpUrl = "http://localhost:3000"
    newapi_admin_token: str = ""
    newapi_username: str = ""
    newapi_password: str = ""
    newapi_session_cookie: str = ""
    newapi_user_id: str = ""
    newapi_login_path: str = "/api/user/login"
    newapi_channel_list_path: str = "/api/channel/"
    newapi_fetch_channel_models_path: str = "/api/channel/fetch_models/{channel_id}"
    newapi_channel_models_path: str = "/api/channel/models"
    newapi_channel_page_size: int = Field(default=100, ge=1)
    newapi_api_key: str = ""

    sync_interval_seconds: int = Field(default=900, ge=30)
    sync_on_startup: bool = True
    enable_background_sync: bool = True
    http_timeout_seconds: int = Field(default=60, ge=1)
    retry_status_codes: str = "403,429,500,502,503,504"

    @property
    def relay_api_key(self) -> str:
        return self.newapi_api_key or self.newapi_admin_token

    @property
    def retry_status_code_set(self) -> set[int]:
        return {int(item.strip()) for item in self.retry_status_codes.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
