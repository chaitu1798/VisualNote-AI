from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "VisualNote AI"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000

    # PostgreSQL Database URL (psycopg3 adapter)
    DATABASE_URL: str = "postgresql+psycopg://visualnote:visualnote@localhost:5432/visualnote"

    # Redis URL
    REDIS_URL: str = "redis://localhost:6379/0"

    # Authentication & Security
    AUTH_SECRET: str = "change-this-to-a-secure-secret-key-in-development-12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Storage Settings
    STORAGE_PROVIDER: str = "local"
    STORAGE_BUCKET: str = "visualnote"
    STORAGE_LOCAL_DIR: str = "storage"

    # AI & Pipeline Settings (Phase 1)
    MOCK_AI: bool = True
    AI_PROVIDER: str = "mock"  # mock, openai, gemini
    TRANSCRIPTION_PROVIDER: str = "mock"  # mock, whisper
    OPENAI_API_KEY: Union[str, None] = None
    GEMINI_API_KEY: Union[str, None] = None
    MAX_UPLOAD_SIZE_MB: int = 100
    DEFAULT_THEME: str = "clean_handwritten"  # clean, clean_handwritten, notebook, chalkboard, minimal
    BROWSER_EXECUTABLE_PATH: Union[str, None] = None  # Optional custom Chromium / Edge path


settings = Settings()
