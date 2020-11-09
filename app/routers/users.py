from fastapi import APIRouter, Depends, HTTPException, Form, Response
from typing import Optional, List
from app.models import User
from app.schemas import User as UserSchema, UserForm
from sqlalchemy.orm import Session
from app import get_db, get_current_user, get_settings
import requests

router = APIRouter()


@router.get("/", response_model=UserSchema)
async def get_user(session: Session= Depends(get_db),
                   user: User = Depends(get_current_user)
                  ):
    """
    View your account info.  
    Look below at the **Example Value** for **Code 200** to see what values to expect.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint below  
    Click **Try it out** and then **Execute**.
    """
    return user

@router.get("/all", response_model=List[UserSchema], include_in_schema=False)
async def get_users(
                    session:Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                   )-> UserSchema:
    if not user.is_admin:
        raise HTTPException(403, detail="You do not have permission for this endpoint")

    users:User = session.query(User).all()

    return users

@router.post("/", response_model=UserSchema)
async def create_user(form:UserForm = Depends(UserForm), 
                      session:Session =Depends(get_db)
                     ):
    """
    Create an account using your Twitter _username_, _password_ and _full name_.  
    Afterwards, click the padlock icon anywhere to login.  
    To use Twitter, go to **Twitter Login Step 1** to connect your Twitter, and **Step 2** to verify
    """
    user = User(**form.__dict__)
    session.add(user)
    session.commit()

    # url = "http://127.0.0.1:5000"
    # r = requests.post("http://127.0.0.1:8000", data=form.__dict__)
    # print(r.json())

    return user

@router.put("/", response_model=UserSchema, response_model_exclude=["tweets"], response_model_exclude_unset=True)
async def update_user(username: Optional[str] = Form(None, min_length=3),
                    full_name: Optional[str] = Form(None, min_length=3, alias="full name"),
                    password: Optional[str] = Form(None, min_length=7),
                    session: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                    ):
    """
    Edit your _username_, _full name_ or _password_.  
    **BEWARE!** It's not a good idea to change your _username_ if you're already logged in with Twitter.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint below  
    Click **Try it out** and then **Execute**.
    """
    if username:
        user.username = username

    if full_name:
        user.full_name = full_name

    if password:
        same_password = user.verify_password(password)

        if same_password:
            raise HTTPException(404, detail="Cannot set current password as new password")

        user.set_password(password)
    
    if not (username or full_name or password):
        raise HTTPException(400, detail="Please enter at least one parameter")
    
    session.commit()

    return user


@router.delete("/", status_code=204)
async def delete_user(user: User = Depends(get_current_user),
                      session:Session = Depends(get_db)
                     ):
    """
    Delete your account.  
    You have to be logged in to use this, click the padlock icon to login, or sign up with the **Create User** endpoint above.  
    Click **Try it out** and then **Execute**.
    """
    session.delete(user)
    session.commit()

    return
