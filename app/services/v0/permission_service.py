from functools import wraps

from fastapi import HTTPException

from app.core.database import DataBase


class PermissionService:
    @staticmethod
    async def has_permission(user_id: str, server_id: str, required_permissions: list[str]) -> bool:
        query = """
        SELECT EXISTS (
            -- Check if user has permission via a role
            SELECT 1
            FROM server_user_roles sur
            JOIN server_roles sr ON sr.id = sur.role_id
            JOIN server_role_permissions srp ON srp.role_id = sr.id
            JOIN server_permissions sp ON sp.id = srp.permission_id
            WHERE sur.user_id = $1
            AND sr.server_id = $2
            AND sp.name = ANY($3::text[])
        ) OR EXISTS (
            -- Check if user has permission directly (user-specific permission)
            SELECT 1
            FROM server_user_permissions sup
            JOIN server_permissions sp ON sp.id = sup.permission_id
            WHERE sup.user_id = $1
            AND sp.name = ANY($3::text[])
        ) OR EXISTS (
            -- Check if user is the owner of the server
            SELECT 1
            FROM servers
            WHERE id = $2
            AND owner_id = $1
        )
        """
        return await DataBase.fetchval(query, user_id, server_id, required_permissions)


# Decorator to check permissions
def check_permissions(required_permissions: list[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            server_id = kwargs.get("server_id")
            current_user = kwargs.get("current_user")

            # Ensure required permissions are checked
            if not await PermissionService.has_permission(current_user["id"], server_id, required_permissions):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            # Call the original function with the same arguments
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# staff wrapper
async def is_staff(user_id: str, role: str) -> bool:
    query = "SELECT EXISTS (SELECT 1 FROM staff WHERE id = $1 AND role = $2)"
    return await DataBase.fetchval(query, user_id, role)


def staff_required(allowed_roles: list[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=403, detail="User is not authenticated")
            user_role = current_user.role
            if user_role not in allowed_roles:
                raise HTTPException(status_code=403, detail="User does not have the required role")
            # Additionally check that the user exists in the staff table with that role
            if not await is_staff(current_user.id, user_role):
                raise HTTPException(status_code=403, detail="User is not authorized as staff")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
