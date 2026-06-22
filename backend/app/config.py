from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "placeholder_key"
    DATABASE_URL: str = "sqlite:///./kavach.db"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = "../.env"

settings = Settings()
