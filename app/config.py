from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URI: str
    SECRET_KEY: str
    API_KEY: str
    API_SECRET: str
    BEARER_TOKEN: str
    HOMEPAGE: str
    DOC: str

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()



