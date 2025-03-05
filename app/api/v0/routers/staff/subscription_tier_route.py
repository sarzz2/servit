from fastapi import APIRouter, Depends
from redis import Redis
from starlette.responses import JSONResponse

from app.core.dependencies import get_current_staff, get_redis
from app.models.staff.staff import StaffOut
from app.models.staff.subscription_tier import (
    SubscriptionTierIn,
    SubscriptionTierUpdate,
)
from app.services.v0.permission_service import staff_required
from app.services.v0.staff.subscription_tier_service import (
    activate_subscription_product,
    create_subscription_price,
    create_subscription_product,
    delete_subscription_product,
    get_subscription_tiers,
    update_subscription_tier,
)

router = APIRouter(dependencies=[Depends(get_current_staff)])


@router.get("/tiers")
async def get_all_tiers(
    redis: Redis = Depends(get_redis),
):
    """Get list of all the subscription tiers"""
    return await get_subscription_tiers(redis)


@router.post("/create-tier")
@staff_required(["superadmin", "admin"])
async def create_tier(
    subscription: SubscriptionTierIn,
    current_user: StaffOut = Depends(get_current_staff),
    redis: Redis = Depends(get_redis),
):
    """Create a new subscription tier"""
    try:
        res = await create_subscription_product(redis, subscription.name, subscription.description)
        await create_subscription_price(res, subscription.price, subscription.currency)
        return JSONResponse({"message": "Tier created successfully"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.delete("/{product_id}")
@staff_required(["superadmin", "admin"])
async def delete_tier(
    product_id: str,
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    """Soft Delete a subscription tier"""
    try:
        await delete_subscription_product(redis, product_id)
        return JSONResponse({"message": "Tier deleted successfully"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.patch("/reactivate/{product_id}")
@staff_required(["superadmin", "admin"])
async def reactivate_tier(
    product_id: str,
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    """Undo Soft Deleting a subscription tier"""
    try:
        await activate_subscription_product(redis, product_id)
        return JSONResponse({"message": "Tier activated successfully"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.patch("/update-tier/{tier_id}")
@staff_required(["superadmin", "admin"])
async def update_subscription(
    tier_id: int,
    tier: SubscriptionTierUpdate,
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    try:
        return await update_subscription_tier(redis, tier_id, tier)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
