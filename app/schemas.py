from pydantic import BaseModel, Field, root_validator
from typing import List, Optional

from fastapi import Form
from datetime import datetime


class TweetModel(BaseModel):
    created_at: datetime = Field(..., alias="created at")
    id: str = Field(..., example=1324131697017933824, type="number")
    text: str = Field(..., example="This is a Tweet from Mars")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

class User(BaseModel):
    twitter_id: Optional[str] = Field(None, example=52713870019, alias="twitter id")
    username: str = Field(..., example="Red")
    full_name: Optional[str] = Field(None, example="Color Red", alias="full name", title="full name")
    active: Optional[bool] 
    requests_made: Optional[int] = Field(None, alias="requests made")
    tweets: Optional[List[TweetModel]]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class UserForm:

    def __init__(self,
                username:str = Form(..., min_length=3, description="Your Twitter username preferably"),
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
    location: Optional[str]
    description: Optional[str]
    protected: Optional[bool]
    following: Optional[bool] = Field(None, alias="you follow")
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
    id: str
    text: str
    source: Optional[str]
    user: TwitterUser
    place: Optional[str]
    is_quote_status: bool = Field(..., alias="tweet is a quote")
    retweet_count: int = Field(..., alias="retweets")
    favorite_count: int = Field(..., alias='favorites')
    favorited: Optional[bool]
    retweeted: Optional[bool]
    possibly_sensitive: Optional[bool] = Field(None, alias="possibly sensitive")
    lang: str = Field(..., alias="language")
    # user_mentions: Optional[List[TwitterUser]] = Field(None, alias="users mentioned")

    # @root_validator(pre=True)
    # def unpack(cls, values:dict):
    #     # print(values)
    #     if not "users_mentioned" in values:
    #         print(1)
    #         if values.get("entities"):
    #             print(2)
    #             if values["entities"].get("user_mentions"):
    #                 print(3)
    #                 values["user_mentions"] = values["entities"]["user_mentions"]
    #                 print(values["user_mentions"])
            

    class Config:
        allow_population_by_field_name = True

class TwitterLink(BaseModel):
    id: str = Field(..., example=1325888640115937283, format="int64")
    username: str = Field(..., example="redDevv")