from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "PulsePilot AI"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "pulsepilot"
    jwt_secret: str = "development-secret-change-me"
    
    # Default AI Provider ("gemini" or "ollama")
    ai_provider: str = "gemini"
    
    # Google Gemini Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
