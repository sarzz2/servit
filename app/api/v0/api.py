from fastapi import APIRouter

from .routers import (
    categories_route,
    channels_route,
    friend_requests_route,
    server_notifications_route,
    server_permissions_route,
    server_roles_route,
    servers_route,
    subscription_request,
    users_route,
)
from .routers.staff import staff_route, subscription_tier_route

api_router = APIRouter()

api_router.include_router(users_route.router, prefix="/users", tags=["users"])
api_router.include_router(servers_route.router, prefix="/servers", tags=["servers"])
api_router.include_router(server_notifications_route.router, prefix="/servers/notification", tags=["servers"])
api_router.include_router(categories_route.router, prefix="/category", tags=["categories"])
api_router.include_router(server_roles_route.router, prefix="/roles", tags=["roles"])
api_router.include_router(friend_requests_route.router, prefix="/friends", tags=["friends"])
api_router.include_router(channels_route.router, prefix="/channels", tags=["channels"])
api_router.include_router(server_permissions_route.router, prefix="/permission", tags=["permissions"])
api_router.include_router(subscription_request.protected_router, prefix="/subscription", tags=["subscription"])
api_router.include_router(subscription_request.router, prefix="/subscription", tags=["subscription"])
# staff api
api_router.include_router(staff_route.router, prefix="/staff", tags=["staff"])
api_router.include_router(staff_route.unprotected_router, prefix="/staff", tags=["staff"])
api_router.include_router(subscription_tier_route.router, prefix="/staff/subscription", tags=["staff"])
