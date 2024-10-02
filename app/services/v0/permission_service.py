from app.core.database import DataBase


class PermissionService:
    @staticmethod
    async def has_permission(user_id: str, server_id: str, required_permissions: list[str]) -> bool:
        query = """
        SELECT EXISTS (
            SELECT 1
            FROM server_user_roles sur
            JOIN server_roles sr ON sr.id = sur.role_id
            JOIN server_role_permissions srp ON srp.role_id = sr.id
            JOIN server_permissions sp ON sp.id = srp.permission_id
            WHERE sur.user_id = $1
            AND sr.server_id = $2
            AND sp.name = ANY($3::text[])
        ) OR EXISTS (
            SELECT 1
            FROM servers
            WHERE id = $2
            AND owner_id = $1
        )
        """
        return await DataBase.fetchval(query, user_id, server_id, required_permissions)
