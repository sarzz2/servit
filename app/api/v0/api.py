from fastapi import APIRouter

from .routers import (
    categories_route,
    friend_requests_route,
    server_roles_route,
    servers_route,
    users_route,
    channels_route,
)

api_router = APIRouter()

api_router.include_router(users_route.router, prefix="/users", tags=["users"])
api_router.include_router(servers_route.router, prefix="/servers", tags=["servers"])
api_router.include_router(categories_route.router, prefix="/category", tags=["categories"])
api_router.include_router(server_roles_route.router, prefix="/roles", tags=["roles"])
api_router.include_router(friend_requests_route.router, prefix="/friends", tags=["friends"])
api_router.include_router(channels_route.router, prefix="/channels", tags=["channels"])
