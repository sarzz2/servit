from fastapi import APIRouter

from .routers import servers_route, users_route

api_router = APIRouter()

api_router.include_router(users_route.router, prefix="/users", tags=["users"])
api_router.include_router(servers_route.router, prefix="/servers", tags=["servers"])
