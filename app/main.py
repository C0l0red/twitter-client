from fastapi import FastAPI, Depends, Header, HTTPException
# from sqlalchemy.orm import Session
# from . import database, models, config, schemas, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from . import login, schemas
# from datetime import timedelta
# from functools import lru_cache
# from .models import Base
# from .config import Settings
# from .database import engine, SessionLocal

# models.Base.metadata.create_all(bind=database.engine)

# def get_db():
#     session: Session = database.SessionLocal()
#     try:
#         yield session
#     finally:
#         session.close()

# @lru_cache
# def get_settings():
#     return config.Settings()

app = FastAPI()

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form: OAuth2PasswordRequestForm = Depends()):
    return login(form)
    # user: models.User = models.User.authenticate(form.username, form.password)
    
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # access_token = create_access_token(
    #     data={"sub": user.username}, expires_delta=access_token_expires
    # )
    # token = schemas.Token(access_token=access_token)

    # return token

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