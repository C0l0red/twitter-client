from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

# from .models import User
# from .schemas import User as UserSchema, Token
# from app.main import get_db
# from sqlalchemy.orm import Session

from sqlalchemy.orm import Session
from . import database, models
from .config import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3600

models.Base.metadata.create_all(bind=database.engine)

def get_db():
    session: Session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# router = APIRouter()

def create_access_token(data: dict, 
                        expires_delta: Optional[timedelta] = None,
                        # config: config.Settings = Depends(get_settings)
                        ):
    config: config.Settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def login(form):
    user: models.User = models.User.authenticate(form.username, form.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    token = schemas.Token(access_token=access_token)

    return token

async def get_current_user(
                        token: str = Depends(oauth2_scheme), 
                        session: Session = Depends(get_db)
                        )->models.User:
    config: config.Settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user: models.User = session.query(models.User).filter(models.User.username.ilike(username)).one_or_none()
    if user is None:
        raise credentials_exception
    # if not user.active:
    #     raise HTTPException(403, detail="Inactive user")

    return user