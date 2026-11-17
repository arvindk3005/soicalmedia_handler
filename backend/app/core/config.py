from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "PulsePilot AI"
    database_url: str = "sqlite:///./pulsepilot.db"
    jwt_secret: str = "development-secret-change-me"
    ai_provider: str = "demo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
