import logging
from datetime import datetime

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from redis.asyncio import Redis
from starlette import status

from app.api.v0.routers import limiter
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    create_sudo_token,
    create_verification_token,
    verify_password,
    verify_token,
    verify_verification_token,
)
from app.core.config import settings
from app.core.dependencies import get_current_user, get_redis, get_sudo_user
from app.core.email import MailgunService
from app.models.user import (
    ChangePassword,
    SudoUserModel,
    UserIn,
    UserLogin,
    UserModel,
    UserUpdate,
)
from app.services.v0.user_service import (
    authenticate_user,
    register_user,
    update_user_password,
    verify_user,
)

log = logging.getLogger("fastapi")

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
mailgun_service = MailgunService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, background_tasks: BackgroundTasks):
    """
    Register a new user
    """
    try:
        user_id = await register_user(user.username, user.email, user.password)
        verification_token = create_verification_token(
            {"sub": str(user.username), "id": str(user_id), "email": user.email}
        )
        background_tasks.add_task(
            mailgun_service.send_verification_email, user.email, verification_token, user.username
        )
    except asyncpg.UniqueViolationError as e:
        raise HTTPException(status_code=400, detail=e.detail)
    return {"message": "Registration successful. Please check your email for verification."}


@router.get("/verify-email/{token}")
async def verify_email(token: str):
    payload = verify_verification_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user_id = payload.get("id")
    username = payload.get("sub")
    await verify_user(username)
    access_token = create_access_token(data={"sub": username, "id": user_id})
    refresh_token = create_refresh_token(data={"sub": username, "id": user_id})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/resend-verification")
@limiter.limit("2/30minute")
async def resend_verification(request: Request, email: str, background_tasks: BackgroundTasks):
    user = await UserModel.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user["is_verified"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

    verification_token = create_verification_token({"sub": str(user["id"]), "email": user["email"]})

    background_tasks.add_task(
        mailgun_service.send_verification_email, user["email"], verification_token, user["username"]
    )
    return {"message": "Verification email resent successfully"}


@router.post("/login")
async def login(user: UserLogin):
    """
    Login a user
    """
    user = await authenticate_user(user.username, user.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user["username"], "id": str(user["id"])})
    refresh_token = create_refresh_token(data={"sub": user["username"], "id": str(user["id"])})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/token/refresh")
async def validate_refresh_token(refresh_token: str = Header(...), redis: Redis = Depends(get_redis)):
    """
    Endpoint to refresh access token
    """
    token_data = await verify_token(refresh_token, token_type="refresh")
    logout_timestamp = await redis.get(f"logout_all:{token_data.id}")

    if logout_timestamp is not None:
        # Calculate issuance time based on the refresh token's expiration
        issuance_time = token_data.exp - settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        if issuance_time <= int(logout_timestamp):
            raise HTTPException(
                status_code=401, detail="Refresh token is invalid because the user has logged out from all devices."
            )

    return {
        "access_token": create_access_token(data={"sub": token_data.username, "id": str(token_data.id)}),
        "refresh_token": create_refresh_token(data={"sub": token_data.username, "id": str(token_data.id)}),
    }


@protected_router.post("/token/sudo")
async def get_sudo_token(user: UserLogin):
    """
    Endpoint to obtain a short-lived sudo token
    """
    user = await authenticate_user(user.username, user.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Issue a sudo token with a short expiration
    sudo_token = create_sudo_token(data={"sub": user["username"], "id": str(user["id"])})
    return {"sudo_token": sudo_token}


@protected_router.get("/me", response_model=UserModel)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current user
    """
    return current_user


@protected_router.get("/search/{query}")
async def search_user(query: str, current_user: UserModel = Depends(get_current_user)):
    """
    Search for a user
    """
    users = await UserModel.search_user(query, current_user["id"])
    return users


@protected_router.patch("/update")
async def update_current_user(request: Request, current_user: UserModel = Depends(get_current_user)):
    """
    Update user
    """
    update_data = await request.json()
    try:
        user = await UserUpdate.update_user(current_user["id"], **update_data)
    except asyncpg.UniqueViolationError as e:
        raise HTTPException(status_code=400, detail=e.detail)
    return user


@router.patch("/change_password")
async def change_user_password(
    change_password: ChangePassword,
    current_user: SudoUserModel = Depends(get_sudo_user),
):
    # Verify the current password
    current_user_password = await SudoUserModel.get_user(current_user["id"])
    if not verify_password(change_password.current_password, current_user_password["password"]):
        log.debug("ge")
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    await update_user_password(change_password.new_password, current_user["id"])

    return {"detail": "Password changed successfully."}


@protected_router.post("/logout/all")
async def logout_all(current_user: UserModel = Depends(get_current_user), redis: Redis = Depends(get_redis)):
    """
    Logout user from all devices
    """
    logout_timestamp = int(datetime.now().timestamp())
    await redis.set(
        f"blacklist:access:{current_user["id"]}", logout_timestamp, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    await redis.set(
        f"logout_all:{current_user["id"]}", logout_timestamp, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return {"detail": "User logged out from all devices."}


router.include_router(protected_router)
