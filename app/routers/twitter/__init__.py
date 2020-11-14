import re
import requests

from fastapi import APIRouter, HTTPException, Depends, Query
from requests_oauthlib import OAuth1

from app import get_settings, get_db, get_current_user, Session
from app.models import User
from app.schemas import TwitterLink
from app.config import Settings
from . import tweets, users


router = APIRouter()

def request_token(
                  config: Settings = Depends(get_settings)
                 )-> str:
    url = 'https://api.twitter.com/oauth/request_token'
    auth = OAuth1(client_key=config.API_KEY, client_secret=config.API_SECRET, callback_uri="oob")

    r = requests.post(url, auth=auth)
    if not r.ok:
        raise HTTPException(400, detail="r is not ok")
    
    text = r.text
    token, secret, callback =  [x.split("=")[1] for x in  text.split("&")]
    if callback != "true":
        raise HTTPException(400, detail= "Callback is not true")
    
    return token


@router.get("/login")
async def twitter_login_step_1(
                               token: str = Depends(request_token),
                               user: User = Depends(get_current_user),
                               session: Session = Depends(get_db)
                              )-> dict:
    """
    Step 1 in the Twitter Login.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.  
    Copy the generated URL and paste it in a new tab, login with Twitter and **Authorize this app**.  
    You'll get a PIN which you'll use in **Twitter Login Step 2** below.
    """
    user.oauth_token = token
    session.commit()
    authorize_url = f'https://api.twitter.com/oauth/authorize?oauth_token={token}'


    return {"message": "Go to the URL to login with Twitter. Open in a new tab. You'll get a pin after logging in, use that pin in 'Twitter Login Step 2'",
            "url": authorize_url}

@router.get("/verify")
async def twitter_login_step_2(verifier:int = Query(...), 
                    session: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                    )-> dict:
    """
    Step 2 in the Twitter Login.  
    You must have gotten a PIN from Twitter after Authorizing this app, enter that pin as the _verifier_.   
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    Once it's successful, you can try the other endpoints like **Make Tweet**
    """ 
    oauth_token = user.oauth_token
    if not oauth_token:
        raise HTTPException(400, detail="It seems you've not completed step one. Please go back and complete it.")
    url = "https://api.twitter.com/oauth/access_token"
    params = {"oauth_token": oauth_token,
            "oauth_verifier": verifier}
    r = requests.post(url, params=params)
    if not r.ok:
        if str(verifier)[0] == 0:
            raise HTTPException(400, detail="The verifier token seems to be bad, please repeat Step 1")
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again", "error": r.text})
    
    old_username = user.username.casefold()
    token, secret, twitter_id, username = [x.split("=")[1] for x in  r.text.split("&")]

    user.token = token
    user.token_secret = secret
    user.twitter_id = int(twitter_id)
    user.username = username
    user.oauth_token = None
    user.active = True

    try:
        session.commit()
    except Exception as e:
        raise HTTPException(400, detail="Something seems to have went wrong with updating your account. Please try again")

    if user.username.casefold() != old_username:
        return {"success": f"Your Twitter login is complete, your username has been changed from '{old_username}' to '{user.username}'"}
    
    return {"success": f"Your Twitter login is complete, you can now use Twitter from here"}

@router.get("/convert-link-to-id", response_model=TwitterLink)
async def get_tweet_id_from_link(
            link: str = Query(..., regex="https://twitter.com/([\w_]+)/status/([\d]+)")#, regex="https:")
            ):
    """
    Copy the link of a Tweet and paste it here to get it's _id_.  
    **Hint:** it has to look like **'https://twitter.com/\<username\>/status/\<id\>'** to be valid
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    regex = re.match("https://twitter.com/(?P<username>[\w]+)/status/(?P<id>[\d]+)",link)
    id = regex.group("id")
    username = regex.group("username")

    return TwitterLink(id=id, username=username)

router.include_router(tweets.router, tags=["twitter tweets"])
router.include_router(users.router, tags=["twitter users"])