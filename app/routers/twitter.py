from fastapi import APIRouter, Depends, HTTPException, Path, Query
# from fastapi.responses import JSONResponse
# from sqlalchemy.orm import Session
# from app.main import get_db
from ..models import User, Tweet
from ..schemas import Tweet as TweetSchema, TwitterUser

import requests
from requests_oauthlib import OAuth1
# from .auth import get_current_user
from app import Session, get_settings, get_db, get_current_user
from app.config import Settings
from pprint import pprint
from typing import List, Optional, Union


# auth = OAuth1(client_key=API_KEY, client_secret=API_SECRET, resource_owner_key= "", resource_owner_secret="")

router = APIRouter()

def request_token(
                  config: Settings = Depends(get_settings)
                 )-> str:
    url = 'https://api.twitter.com/oauth/request_token'
    auth = OAuth1(client_key=config.API_KEY, client_secret=config.API_SECRET, callback_uri="oob")

    r = requests.post(url, auth=auth)
    if not r.ok:
        raise HTTPException(400, detail="r is not ok")
    
    # print(r.text())
    text = r.text
    token, secret, callback =  [x.split("=")[1] for x in  text.split("&")]
    if callback != "true":
        raise HTTPException(400, detail= "Callback is not true")
    
    # authorize_url = f'https://api.twitter.com/oauth/authorize?oauth_token={token}' 
    return token
# request_token()


@router.get("/login")
async def twitter_login_step_1(
                               token: str = Depends(request_token),
                               user: User = Depends(get_current_user),
                               session: Session = Depends(get_db)
                              )-> dict:
    user.oauth_token = token
    session.commit()
    authorize_url = f'https://api.twitter.com/oauth/authorize?oauth_token={token}'


    return {"message": "Go to the URL to login with Twitter. Open in a new tab. You'll get a pin after logging in, use that pin in 'Twitter Login Step 2'",
            "url": authorize_url}

@router.get("/verify")
async def twitter_login_step_2(oauth_verifier:str, 
                    session: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                    )-> dict:
    oauth_token = user.oauth_token
    if not oauth_token:
        raise HTTPException(400, detail="It seems you've not completed step one. Please go back and complete it.")
    url = "https://api.twitter.com/oauth/access_token"
    params = {"oauth_token": oauth_token,
            "oauth_verifier": oauth_verifier}
    r = requests.post(url, params=params)
    if not r.ok:
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again", "error": r.text})
    
    old_username = user.username.casefold()
    token, secret, twitter_id, username = [x.split("=")[1] for x in  r.text.split("&")]

    user.token = token
    user.token_secret = secret
    user.twitter_id = twitter_id
    user.username = username
    user.oauth_token = None
    user.active = True

    try:
        session.commit()
    except Exception as e:
        raise HTTPException(400, detail="Something seems to have went wrong with updating your account. Please try again")
    # else:
    #     session.rollback()
    #     user.oauth_token = oauth_token
    #     session.commit()

    if user.username.casefold() != old_username:
        return {"success": f"Your Twitter login is complete, your username has been changed from '{old_username}' to '{user.username}'. Please login again to use Twitter here"}
    
    return {"success": f"Your Twitter login is complete, you can now use Twitter from here"}

# def get_oauth1_token(user:User):
#     config: Settings = get_settings()
#     auth = OAuth1(config.API_KEY, 
#                   config.API_SECRET,
#                   user.token,
#                   user.token_secret
#                  )
#     return auth

@router.get("/make_tweet", response_model=TweetSchema)
async def make_tweet(tweet: str,
                     user: User = Depends(get_current_user),
                     session: Session = Depends(get_db)
                     )-> TweetSchema:

    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to make tweets")

    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = dict(status=tweet)
    auth = user.get_oauth1_token()

    r = requests.post(url, params=params, auth=auth)
    if not r.ok:
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                        "error from twitter": r.text})
    tweet = r.json()

    new_tweet = Tweet(**tweet)
    # new_tweet.created_at = datetime.strptime(new_tweet.created_at, "%a %b %d %H:%M:%S %z %Y")
    user.tweets.append(new_tweet)
    session.commit()
    return tweet

@router.get("/get_tweet/{id}", response_model=TweetSchema)
def get_tweet(
              id: int, 
              user: User = Depends(get_current_user),
              config: Settings = Depends(get_settings)
             )-> TweetSchema:
    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to view tweets")

    url = "https://api.twitter.com/1.1/statuses/show.json"
    params = dict(id=id, include_entities=True)
    auth = user.get_oauth1_token()
    # headers = dict(Authorization=f"Bearer {config.BEARER_TOKEN}")

    r = requests.get(url, params=params, auth=auth)
    if not r.ok:
         raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                        "error from twitter": r.text})

    tweet = r.json()
    pprint(tweet)
    return tweet

@router.get("/get_users", response_model=Union[TwitterUser, List[TwitterUser]])
async def get_users(
                    ids: Optional[List[int]] = Query(None),
                    usernames: Optional[List[str]] = Query(None),
                    user: User = Depends(get_current_user)
                   ):
    if usernames:
        usernames = ",".join(usernames)
        url = "https://api.twitter.com/2/users/by"
        params = {"usernames": usernames, "user.fields":"created_at,description,location,username,protected,entities",
                  "expansions": "pinned_tweet_id"}
        
    elif ids:
        # ids = [str(x) for x in ids]
        ids = ",".join([str(x) for x in ids])
        url = "https://api.twitter.com/2/users"
        params = {"ids":ids, "user.fields":"created_at,description,location,username,protected,entities",
                  "expansions": "pinned_tweet_id"}
    
    else:
        raise HTTPException(400, detail="Please enter an id or username")
    
    auth = user.get_oauth1_token()

    r = requests.get(url, params=params, auth=auth)
        
    
    if not r.ok:
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                    "error from twitter": r.text})
    
    data = r.json()['data']
    # print(data)
    if len(data) == 1:
        # print(data[0])
        return data[0]
    else:
        return data
# "1324131697017933824"
# "976206484467052544" "2713870019"