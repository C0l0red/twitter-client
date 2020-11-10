from fastapi import APIRouter, Depends, HTTPException, Path, Query
from ..models import User, Tweet
from ..schemas import Tweet as TweetSchema, TwitterUser, TwitterLink
import re

import requests
from requests_oauthlib import OAuth1
from app import Session, get_settings, get_db, get_current_user
from app.config import Settings
from pprint import pprint
from typing import List, Optional, Union



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


@router.get("/make-tweet", response_model=TweetSchema)
async def make_tweet(tweet: str,
                     user: User = Depends(get_current_user),
                     session: Session = Depends(get_db)
                     )-> TweetSchema:
    """
    Make a Tweet, enter a _tweet_.
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
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
    user.tweets.append(new_tweet)
    user.requests_made += 1

    session.commit()
    return tweet

@router.get("/get-tweets", response_model=Union[TweetSchema, List[TweetSchema]])
def get_tweets(
              ids: List[int] = Query(...), 
              user: User = Depends(get_current_user),
              config: Settings = Depends(get_settings),
              session: Session = Depends(get_db)
             )-> TweetSchema:
    """
    View Tweets using their _ids_.  
    **How To Get The ID Of A Tweet:**  
    - Copy the link to the Tweet, the ID is the long number there.  
    - **OR** Copy the link to the Tweet and paste it in the **Get Tweet ID From Link** endpoint

    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to view tweets")
    
    ids = ",".join([str(x) for x in ids])
    params = dict(id=ids, include_entities=True)

    url = "https://api.twitter.com/1.1/statuses/lookup.json"
    auth = user.get_oauth1_token()

    r = requests.get(url, params=params, auth=auth)
    if not r.ok:
         raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                        "error from twitter": r.text})
    user.requests_made += 1
    session.commit()

    tweets = r.json()

    if len(tweets) == 1:
        return tweets[0]
    return tweets

@router.get("/get-users", response_model=Union[TwitterUser, List[TwitterUser]])
async def get_users(
                    ids: Optional[List[int]] = Query(None),
                    usernames: Optional[List[str]] = Query(None),
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_db)
                   ):
    """
    Get single or multiple Twitter Users using their _usernames_ or _ids_.  
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """

    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to view users")

    usernames = ",".join(usernames) if usernames else usernames
    ids = ",".join([str(x) for x in ids]) if ids else ids

    if not (usernames or ids):
        raise HTTPException(400, detail="Please enter an id or username")

    url = "https://api.twitter.com/1.1/users/lookup.json"
    params = dict(screen_name=usernames,user_id=ids)
    auth = user.get_oauth1_token()
    
    r = requests.get(url, params=params, auth=auth)
        
    if not r.ok:
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                    "error from twitter": r.text})
    user.requests_made += 1
    session.commit()

    data = r.json()
    if len(data) == 1:
        return data[0]
    else:
        return data

@router.get("/convert-link-to-id", response_model=TwitterLink)
async def get_tweet_id_from_link(
            link: str = Query(..., regex="https://twitter.com/([\w_]+)/status/([\d]+)")
            ):
    """
    Copy the link of a Tweet and paste it here to get it's _id_.  
    **Hint:** it has to look like **'https://twitter.com/\<username\>/status/\<id\>'** to be valid
    """
    regex = re.match("https://twitter.com/(?P<username>[\w]+)/status/(?P<id>[\d]+)",link)
    id = regex.group("id")
    username = regex.group("username")

    return TwitterLink(id=id, username=username)
    

