from pydantic import BaseModel, Field
from typing import List, Optional

from fastapi import Form

class User(BaseModel):
    twitter_id: Optional[str] = Field(None, example="52713870019")
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
                password:str = Form(..., min_length=7),
                full_name:Optional[str] = Form(None, alias='full name', min_length=3)
                ):
        self.username = username
        self.password = password
        self.full_name = full_name

class Token(BaseModel):
    access_token: str
    token_type: str = Field("bearer")
