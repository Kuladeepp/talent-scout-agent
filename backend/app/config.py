from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    google_application_credentials: str | None = None

    model_flash: str = "gemini-2.5-flash"
    model_pro: str = "gemini-2.5-pro"
    model_embedding: str = "text-embedding-005"
    model_flash_lite: str = "gemini-2.5-flash-lite"

    anthropic_api_key: str | None = None
    firecrawl_api_key: str | None = None

    top_k_retrieve: int = 10
    top_k_outreach: int = 5
    similarity_floor: float = 0.30
    cache_dir: str = "./data/cache"

    @property
    def cache_path(self) -> Path:
        p = Path(self.cache_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()  # type: ignore[call-arg]
