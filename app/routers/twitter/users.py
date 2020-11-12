import requests
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Union, List, Optional

from app import get_current_user, get_db, get_settings, Session
from app.schemas import TwitterUser
from app.models import User
from app.config import Settings

router = APIRouter()

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