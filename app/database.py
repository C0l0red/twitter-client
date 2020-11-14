from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings, Settings

config: Settings = get_settings()

SQLALCHEMY_DATABASE_URI = config.DATABASE_URI
if config.DATABASE_URI.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URI)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()