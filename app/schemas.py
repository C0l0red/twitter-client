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
    tweets: Optional[list]

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
    name: Optional[str]
    screen_name: str = Field(None, alias="username")
    username: str = Field(None)
    location: Optional[str]
    description: Optional[str]
    protected: Optional[bool]
    following: Optional[bool] = Field(None, alias="following")
    followers_count: Optional[int] = Field(None, alias="followers")
    friends_count: Optional[int] = Field(None, alias="users they follow")
    favourites_count: Optional[int] = Field(None, alias="favourites")
    verified: Optional[bool]
    statuses_count: Optional[int] = Field(None, alias="tweets")
    created_at: Optional[str] = Field(None, alias="created at")

    class Config:
        allow_population_by_field_name = True

class Tweet(BaseModel):
    created_at: str = Field(..., alias="created at")
    id: int
    text: str
    source: Optional[str]
    user: TwitterUser
    place: Optional[str]
    is_quote_status: bool = Field(..., alias="tweet is a quote")
    retweet_count: int = Field(..., alias="retweets")
    favorite_count: int = Field(..., alias='favorites')
    favorited: bool
    retweeted: bool

    class Config:
        allow_population_by_field_name = True
