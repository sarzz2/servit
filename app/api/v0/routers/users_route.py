import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.core.auth import create_access_token
from app.core.dependencies import get_current_user
from app.models.user import UserIn, UserLogin, UserModel
from app.services.v0.user_service import authenticate_user, register_user

log = logging.getLogger("fastapi")

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn):
    """
    Register a new user
    """
    try:
        await register_user(user.username, user.email, user.password)
    except asyncpg.UniqueViolationError as e:
        return {"message": e.detail}
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token}


@router.post("/login")
async def login(user: UserLogin):
    """
    Login a user
    """
    user = await authenticate_user(user.username, user.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@protected_router.get("/me", response_model=UserModel)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current user
    """
    return current_user


router.include_router(protected_router)
