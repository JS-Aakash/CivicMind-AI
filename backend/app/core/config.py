"""
CivicMind AI — Application Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "CivicMind AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DEMO_MODE: bool = True

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://civicmind:civicmind_secret@localhost:5432/civicmind"

    # Models & AI Mode
    AI_MODE: str = "trained"  # "trained" | "demo"
    MODELS_DIR: str = "./models"
    MURIL_MODEL_NAME: str = "google/muril-base-cased"
    MURIL_LOCAL_PATH: str = "./models/muril-base-cased"
    TRAINED_MODEL_PATH: str = "./models/grievance/v1"
    DATASET_DIR: str = "./data"

    # Demo map (Chennai, Tamil Nadu)
    DEMO_MAP_LAT: float = 13.0827
    DEMO_MAP_LNG: float = 80.2707

    # Admin Auth
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "civicmind2026"
    JWT_SECRET_KEY: str = "civicmind-demo-secret-2026"

    # Resolution Geofencing
    RESOLUTION_GEOFENCE_ENABLED: bool = False
    RESOLUTION_GEOFENCE_RADIUS_METERS: float = 200.0

    @property
    def muril_path(self) -> Path:
        return Path(self.MURIL_LOCAL_PATH)

    @property
    def models_dir_path(self) -> Path:
        return Path(self.MODELS_DIR)

    @property
    def trained_model_dir(self) -> Path:
        v1_1_path = Path("./models/grievance/v1.1")
        if (v1_1_path / "config.json").exists() and (v1_1_path / "heads.pt").exists():
            return v1_1_path
        return Path(self.TRAINED_MODEL_PATH)

    @property
    def dataset_dir_path(self) -> Path:
        return Path(self.DATASET_DIR)


settings = Settings()
