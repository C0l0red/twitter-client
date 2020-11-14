import re
import requests

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Union, List, Optional

from app import Session, get_current_user, get_db, get_settings
from app.models import User, Tweet
from app.schemas import Tweet as TweetSchema
from app.config import Settings

router = APIRouter()

@router.get("/make-tweet", response_model=TweetSchema)
async def make_tweet(tweet: str = Query(...),
                    #  attachment_url: Optional[str] = Query(None, alias="link of tweet to quote", regex="https://twitter.com/([\w_]+)/status/([\d]+)"),
                    #  in_reply_to: Optional[int] = Query(None, alias="link of tweet to reply to", regex="https://twitter.com/([\w_]+)/status/([\d]+)"), 
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
    # if in_reply_to:
        # regex = re.match("https://twitter.com/(?P<username>[\w]+)/status/(?P<id>[\d]+)", in_reply_to)
        # status_id = regex.group("id")
    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = dict(status=tweet,
                #   attachment_url=attachment_url,
                #   in_reply_to_status_id=status_id,
                    )
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

@router.get("/reply-tweet", response_model=TweetSchema)
async def reply_tweet(reply: str,
                      in_reply_to: str = Query(None, alias="link of tweet", regex="https://twitter.com/([\w_]+)/status/([\d]+)"),
                      status_id: int = Query(None, alias="id of tweet"),
                      user: User = Depends(get_current_user),
                      session: Session = Depends(get_db)
                     )-> TweetSchema:
    """
    Reply to a Tweet using either it's ID or it's link.  
    **Hint:** it has to look like **'https://twitter.com/\<username\>/status/\<id\>'** to be valid.  
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to make tweets")
    if not (in_reply_to or status_id):
        raise HTTPException(400, detail="Please enter either a Tweet ID or link to reply to")

    if in_reply_to:
        regex = re.match("https://twitter.com/(?P<username>[\w]+)/status/(?P<id>[\d]+)", in_reply_to)
        status_id = regex.group("id")

    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = dict(status=reply,
                  in_reply_to_status_id=status_id,
                  auto_populate_reply_metadata=True
                 )
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

@router.get("/quote-tweet", response_model=TweetSchema)
async def quote_tweet(quoted_reply:str,
                      attachment_url: str = Query(..., alias="link of tweet", regex="https://twitter.com/([\w_]+)/status/([\d]+)"),
                      user: User = Depends(get_current_user),
                      session: Session = Depends(get_db)
                     )-> TweetSchema:
    """
    Quote a Tweet using it's link.  
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    if not user.active:
        raise HTTPException(401, detail="Your account seems to be inactive, please login with twitter to make tweets")

    # regex = re.match("https://twitter.com/(?P<username>[\w]+)/status/(?P<id>[\d]+)", in_reply_to)
    # status_id = regex.group("id")

    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = dict(status=quoted_reply,
                  attachment_url=attachment_url,
                #   auto_populate_reply_metadata=True
                 )
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

@router.get("/home-timeline", response_model=List[TweetSchema])
async def home_timeline(
                        count: Optional[int] = Query(None, le=200),
                        user: User = Depends(get_current_user),
                       )-> TweetSchema:
    """
    View your home timeline.  
    You can optionally use __count__ to choose the amount of tweets to load.  
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    params = dict(count=count, exclude_replies=False, include_entities=True)
    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
    auth = user.get_oauth1_token()

    r = requests.get(url, params=params, auth=auth)
    if not r.ok:
        raise HTTPException(400, detail={"message":"Something went wrong with Twitter, please try again or contact me @redDevv",
                                        "error from twitter": r.text})

    timeline = r.json()
    return timeline