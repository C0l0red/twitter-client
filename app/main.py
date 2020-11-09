from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from . import login, schemas

tags_metadata = [
    {
        "name": "users",
        "description": "Manage your account. Create, edit, view and delete **user**s"
    },
    {
        "name": "twitter",
        "description": "Manage your Twitter account. Login, make and view Tweets and more"
    }
]

app = FastAPI(
              title="Red's Twitter Client",
              description="""A simple web API to use Twitter from.  
                            Endpoints with lock icons require login.  
                            Check out the documentation <a href="/redoc">here</a>""",
              version="1.0",
              openapi_tags=tags_metadata
            )

@app.post("/token", response_model=schemas.Token, include_in_schema=False)
async def login_for_access_token(form: OAuth2PasswordRequestForm = Depends()):
    return login(form)
    

from .routers import users, twitter

# app.include_router(auth.router,
#     prefix="/auth",
#     tags=["auth"])


app.include_router(users.router,
    prefix="/users",
    tags=['users'],
    )

app.include_router(twitter.router,
    prefix="/twitter",
    tags=['twitter'])