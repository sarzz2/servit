import json

from app.core.auth import verify_password
from app.models.staff.staff import StaffCreate, StaffLogin, StaffOut, StaffUpdate


async def authenticate_staff(email, password):
    staff = await StaffLogin.get_staff_by_email(email)
    print(staff)
    if staff and verify_password(password, staff.password):
        return staff
    return None


async def get_staff_list(redis):
    cache_key = "staff_list"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    staff_members = await StaffOut.get_staff()
    serializable_result = [staff.model_dump() for staff in staff_members]
    await redis.set(cache_key, json.dumps(serializable_result, default=str), ex=86400)
    return staff_members


async def create_new_staff(redis, staff):
    await redis.delete("staff_list")
    res = await StaffCreate.create_staff(staff.name, staff.email, staff.phone, staff.role, staff.password)
    if res == "INSERT 0 0":
        raise ValueError("Staff member with the given email id already exists")
    return res


async def update_staff_details(redis, staff_id, staff):
    await redis.delete("staff_list")
    return await StaffUpdate.update_staff(staff_id, staff)
    # return await StaffOut.get_staff_by_id(staff_id)


async def delete_staff_record(redis, staff_id):
    await redis.delete("staff_list")
    res = await StaffUpdate.delete_staff(staff_id)
    return res
