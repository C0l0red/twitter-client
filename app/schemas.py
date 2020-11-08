from pydantic import BaseModel, Field
from typing import List, Optional

from fastapi import Form
from datetime import datetime

# datetime.datetime.strptime("Sun Nov 08 08:29:06 +0100 2020", "%a %b %d %H:%M:%S %z %Y")

class User(BaseModel):
    twitter_id: Optional[str] = Field(None, example="52713870019", alias="twitter id")
    username: str = Field(..., example="Red")
    full_name: Optional[str] = Field(None, example="Color Red", alias="full name", title="full name")
    active: Optional[bool] 
    requests_made: Optional[int] = Field(None, alias="requests made")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class UserForm:

    def __init__(self,
                username:str = Form(..., min_length=3),
                password:str = Form(..., min_length=7, ),
                full_name:Optional[str] = Form(None, alias='full name', min_length=3)
                ):
        self.username = username
        self.password = password
        self.full_name = full_name

class Token(BaseModel):
    access_token: str
    token_type: str = Field("bearer")

class TwitterUser(BaseModel):
    id: str
    name: str
    screen_name: str = Field(..., alias="screen name")
    location: Optional[str]
    description: Optional[str]
    protected: bool
    followers_count: int = Field(..., alias="followers")
    friends_count: int = Field(..., alias="following")
    favourites_count: int = Field(..., alias="favourites")
    verified: bool
    statuses_count: int = Field(..., alias="tweets")
    created_at: datetime = Field(..., alias="created at")

    class Config:
        allow_population_by_field_name = True

class Tweet(BaseModel):
    created_at: str = Field(..., alias="created at")
    id: int
    text: str
    source: str
    user: TwitterUser
    place: str
    is_quote_status: bool = Field(..., alias="tweet is a quote")
    retweet_count: int = Field(..., alias="retweets")
    favourite_count: int = Field(..., alias='favourites')
    favourited: bool
    retweeted: bool

    class Config:
        allow_population_by_field_name = True
