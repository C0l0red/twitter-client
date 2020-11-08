from .database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, Session
# from uuid import uuid4
from passlib.context import CryptContext
from typing import Optional
from sqlalchemy.ext.hybrid import hybrid_property
from .config import Settings, get_settings
from requests_oauthlib import OAuth1
import requests
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# make_id = (lambda : uuid4().hex.upper())

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    full_name = Column(String(50))
    active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    requests_made = Column(Integer, default=0)

    # public_id = Column(String(32), default=make_id)
    twitter_id = Column(String(32))
    oauth_token = Column(String(50))
    token = Column(String(80))
    token_secret = Column(String(80))
    tweets:list = relationship("Tweet", back_populates="user", lazy="dynamic")

    def __init__(self, *, username:str, password:str, full_name:Optional[str]=None, **extra):
        session: Session = SessionLocal()
        taken = session.query(User).filter(User.username.ilike(username)).first()
        session.close()

        if taken:
            return

        self.username = username
        self.full_name = full_name
        self.set_password(password)
        self.is_admin = False

    def set_password(self, password):
        self.password = pwd_context.hash(password)

    def verify_password(self, password)->bool:
        return pwd_context.verify(password, self.password)

    @staticmethod
    def authenticate(username, password):
        session: Session = SessionLocal()
        user:User = session.query(User).filter(User.username.ilike(username)).one_or_none()
        
        session.close()

        if user:
            is_verified = user.verify_password(password)
            if is_verified:
                return user

        return None

    def get_oauth1_token(self):
        config: Settings = get_settings()
        auth = OAuth1(config.API_KEY, 
                    config.API_SECRET,
                    self.token,
                    self.token_secret
                    )
        return auth


class Tweet(Base):
    __tablename__ = "tweet"

    id = Column(Integer, primary_key=True)
    # tweet_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="tweets")

    def __init__(self, id: int, text: str, created_at:str, user=None, **extra):
        self.id = id
        self.text = text
        
        if isinstance(user, dict):
            self.user_id = user['id']
        elif isinstance(user, User):
            self.user = user

        if isinstance(created_at, str):
            try:
                self.created_at=datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            except ValueError:
                self.created_at = datetime.utcnow()
        # self.created_at = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        elif isinstance(created_at, datetime):
            self.created_at = created_at
        else:
            self.created_at = datetime.utcnow()



