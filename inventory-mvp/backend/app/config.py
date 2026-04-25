from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Inventory MVP"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 8
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/inventory_mvp"
    cors_origins: str = "http://localhost:4456"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
