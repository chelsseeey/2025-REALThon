from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://realthon:realthon123@localhost:5432/realthon_db"
    
    class Config:
        env_file = ".env"

settings = Settings()

