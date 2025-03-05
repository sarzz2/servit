from typing import List

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from starlette.responses import JSONResponse

from app.core.auth import create_access_token, create_refresh_token, get_password_hash
from app.core.dependencies import get_current_staff, get_redis
from app.models.staff.staff import StaffCreate, StaffLogin, StaffOut, StaffUpdate
from app.services.v0.permission_service import staff_required
from app.services.v0.staff.staff_service import (
    authenticate_staff,
    create_new_staff,
    delete_staff_record,
    get_staff_list,
    update_staff_details,
)

router = APIRouter(dependencies=[Depends(get_current_staff)])
unprotected_router = APIRouter()


@unprotected_router.post("/login")
async def login(staff: StaffLogin):
    """
    Login a user
    """
    user = await authenticate_staff(staff.email, staff.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    print(user)
    access_token = create_access_token(data={"sub": user.email, "id": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email, "id": str(user.id), "role": user.role})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/", response_model=List[StaffOut])
@staff_required(["superadmin", "admin"])
async def list_staff(
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    """List all staff members"""
    return await get_staff_list(redis)


@router.get("/{staff_id}", response_model=StaffOut)
@staff_required(["superadmin", "admin"])
async def get_staff(
    staff_id: str,
    current_user: StaffOut = Depends(get_current_staff),
):
    """Retrieve a staff member by ID"""
    return await StaffOut.get_staff_by_id(staff_id)


@router.post("/", response_model=StaffOut)
@staff_required(["superadmin", "admin"])
async def create_staff(
    staff: StaffCreate,
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    """Create a new staff member"""
    try:
        staff.password = get_password_hash(staff.password)
        await create_new_staff(redis, staff)
        return staff
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})


@router.patch("/{staff_id}")
async def update_staff(
    staff_id: str,
    staff: StaffUpdate,
    redis: Redis = Depends(get_redis),
    current_user: StaffOut = Depends(get_current_staff),
):
    try:
        if staff_id == current_user.id or current_user.role in ["superadmin", "admin"]:
            await update_staff_details(redis, staff_id, staff)
            return JSONResponse(status_code=200, content={"detail": "Staff member updated successfully"})
        else:
            return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str, redis: Redis = Depends(get_redis), current_user: StaffOut = Depends(get_current_staff)
):
    try:
        if staff_id == current_user.id or current_user.role in ["superadmin", "admin"]:
            await delete_staff_record(redis, staff_id)
            return JSONResponse(status_code=200, content={"detail": "Staff member deleted successfully"})
        else:
            return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
