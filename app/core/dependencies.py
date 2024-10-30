from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from starlette import status

from app.core.auth import verify_token
from app.core.redis import RedisClient
from app.models.user import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
redis_client = RedisClient()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = verify_token(token)
        user = await UserModel.get_user(token_data.id)
        if user is None:
            raise credentials_exception
        return user
    except HTTPException:
        raise credentials_exception


async def get_redis() -> Redis:
    return redis_client.client
