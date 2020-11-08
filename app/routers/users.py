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
    return user

@router.get("/all", response_model=List[UserSchema])
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
    user = User(**form.__dict__)
    session.add(user)
    session.commit()

    # url = "http://127.0.0.1:5000"
    # r = requests.post("http://127.0.0.1:8000", data=form.__dict__)
    # print(r.json())

    return user

@router.put("/", response_model=UserSchema)
async def update_user(username: Optional[str] = Form(None, min_length=3),
                    full_name: Optional[str] = Form(None, min_length=3, alias="full name"),
                    password: Optional[str] = Form(None, min_length=7),
                    session: Session = Depends(get_db),
                    user: User = Depends(get_current_user)
                    ):
    if username:
        user.username = username

    if full_name:
        user.full_name = full_name

    if password:
        same_password = user.verify_password(password)

        if same_password:
            raise HTTPException(404, detail="Cannot set current password as new password")

        user.set_password(password)
    
    session.commit()

    return user

# @router.patch("/", status_code=204)
# async def update_password(password: str = Form(..., min_length=7),
#                         session: Session = Depends(get_db),
#                         user: User = Depends(get_current_user)
#                         ):
#     same_password = user.verify_password(password)
#     if same_password:
#         raise HTTPException(404, detail="Cannot set current password as new password")

#     user.set_password(password)
#     session.commit()

#     return

@router.delete("/", status_code=204)
async def delete_user(user: User = Depends(get_current_user),
                      session:Session = Depends(get_db)
                     ):
    session.delete(user)
    session.commit()

    return
