import json
from typing import List, Optional
from uuid import UUID

from pydantic import Field, constr

from app.core.database import DataBase

validation_query = """
                     WITH
     valid_permissions AS (
                   SELECT id, name FROM server_permissions
                    WHERE id = ANY($1::uuid[])),
   invalid_permissions AS (
                   SELECT unnest($1::uuid[]) AS id
                   EXCEPT
                   SELECT id FROM valid_permissions),
      owner_permission AS (
                   SELECT name
                     FROM valid_permissions
                    WHERE name = 'OWNER')
                   SELECT
                         CASE
                             WHEN (SELECT COUNT(*) FROM invalid_permissions) > 0
                                THEN 'Invalid permission IDs provided.'
                             WHEN (SELECT COUNT(*) FROM owner_permission) > 0
                                THEN 'Cannot assign ''OWNER'' permission to a role.'
                             ELSE 'Valid'
                         END AS error_message;
                 """


class ServerRolesIn(DataBase):
    name: constr(min_length=1, max_length=50) = Field(..., title="Role Name")
    description: constr(min_length=1, max_length=255) = Field(..., title="Role Description")
    color: constr(min_length=6, max_length=7) = Field("#ffffff", title="Role Color")
    permissions: List[str] = Field(default=[], title="Permissions for the Role")

    @classmethod
    async def new_role_with_permissions(
        cls, server_id: UUID, name: str, description: str, color: str, permissions: List[UUID]
    ):
        """
        Create a new server role with permissions.
        """
        # Step 1: Validate permissions
        result = await cls.fetchval(validation_query, permissions)

        # If there was an error, raise an exception
        if result != "Valid":
            raise ValueError(result)

        # Step 2: Insert role and assign permissions
        insertion_query = """
                    WITH inserted_role AS (
             INSERT INTO server_roles (server_id, name, description, color)
                  VALUES ($1, $2, $3, $4)
               RETURNING *
                    )
             INSERT INTO server_role_permissions (role_id, permission_id)
                  SELECT ir.id, vp.id
                    FROM inserted_role ir
                    JOIN server_permissions vp ON vp.id = ANY($5::uuid[]);
        """
        # Execute the query
        return await cls.fetchval(insertion_query, server_id, name, description, color, permissions)

    @classmethod
    async def delete_role(cls, role_id: UUID):
        query = """
                    WITH deleted_user_roles AS (
             -- Remove the role associations from users
             DELETE FROM server_user_roles
                   WHERE role_id = $1
               RETURNING role_id
                        ),
    -- Remove the role's permissions
  deleted_permissions AS (DELETE FROM server_role_permissions
                                WHERE role_id = $1
                            RETURNING permission_id
                        )
             -- Finally, remove the role from the server_roles table
             DELETE FROM server_roles
                   WHERE id = $1
            """
        x = await cls.execute(query, role_id)
        if x == "DELETE 0":
            return False
        return True


class ServerRolesOut(DataBase):
    id: UUID
    name: str
    description: str
    color: str
    permissions: Optional[str]

    @classmethod
    async def get_role(cls, server_id: UUID):
        query = """
        SELECT sr.id, sr.name, sr.description, sr.color,
               json_agg(
                   json_build_object('id', p.id, 'name', p.name)
               ) AS permissions
          FROM server_roles sr
     LEFT JOIN server_role_permissions srp ON sr.id = srp.role_id
     LEFT JOIN server_permissions p ON p.id = srp.permission_id
         WHERE sr.server_id = $1
      GROUP BY sr.id
        """
        result = await cls.fetch(query, server_id)
        for role in result:
            # Ensure permissions are loaded as a list of dictionaries
            if isinstance(role.permissions, str):
                role.permissions = json.loads(role.permissions)
        return result


class ServerRoleUpdate(DataBase):
    name: Optional[constr(min_length=1, max_length=50)] = Field(None, description="Role name")
    description: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Role description")
    color: Optional[constr(min_length=6, max_length=7)] = Field(None, description="Role color")
    permissions: Optional[List[UUID]] = Field(None, description="List of permission IDs")

    @classmethod
    async def update_server_role(cls, role_id: UUID, update_data):
        """Update a server role."""
        base_query = "UPDATE server_roles SET "
        update_fields = []
        values = []

        # Dynamically append fields to be updated
        if update_data.name is not None:
            update_fields.append("name = $" + str(len(values) + 1))
            values.append(update_data.name)
        if update_data.description is not None:
            update_fields.append("description = $" + str(len(values) + 1))
            values.append(update_data.description)
        if update_data.color is not None:
            update_fields.append("color = $" + str(len(values) + 1))
            values.append(update_data.color)

        # If no fields were provided, skip the update
        if not update_fields and not update_data.permissions:
            raise ValueError("At least one field must be provided to update")

        # Finalize the query
        query = base_query + ", ".join(update_fields) + " WHERE id = $" + str(len(values) + 1) + " RETURNING id"
        values.append(role_id)

        await cls.execute(query, *values)

        # Handle updating permissions if provided
        if update_data.permissions is not None:
            # Validate permissions
            result = await cls.fetchval(validation_query, update_data.permissions)

            # If there was an error, raise an exception
            if result != "Valid":
                raise ValueError(result)

            update_permissions_query = """
                   WITH
            -- Remove old permissions that are not in the new list
                       deleted_permissions AS (
            DELETE FROM server_role_permissions
                  WHERE role_id = $1 AND permission_id = ANY(
                 SELECT id FROM server_permissions WHERE id = ANY($2::uuid[]))
                       )
              -- Insert new permissions that are not already assigned
              INSERT INTO server_role_permissions (role_id, permission_id)
                   SELECT $1, p.id
                     FROM server_permissions p
                    WHERE p.id = ANY($2::uuid[]) AND p.id NOT IN (
                   SELECT permission_id FROM server_role_permissions WHERE role_id = $1
                   )
                   RETURNING permission_id;
               """
            await cls.execute(update_permissions_query, role_id, update_data.permissions)
