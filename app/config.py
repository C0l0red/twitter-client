from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URI: str
    SECRET_KEY: str
    API_KEY: str
    API_SECRET: str
    BEARER_TOKEN: str

    class Config:
        env_file = ".env"



