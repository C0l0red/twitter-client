from fastapi import FastAPI, Depends, Header, HTTPException
# from sqlalchemy.orm import Session
# from . import database, models, config, schemas, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from . import login, schemas

app = FastAPI()

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form: OAuth2PasswordRequestForm = Depends()):
    return login(form)
    

from .routers import users, twitter

# app.include_router(auth.router,
#     prefix="/auth",
#     tags=["auth"])


app.include_router(users.router,
    prefix="/users",
    tags=['users'])

app.include_router(twitter.router,
    prefix="/twitter",
    tags=['twitter'])