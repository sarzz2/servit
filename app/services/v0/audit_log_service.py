from datetime import datetime

from app.core.database import DataBase


async def insert_audit_log(user_id: str, entity: str, entity_id: str, action: str, changes: str):
    query = """
    INSERT INTO audit_logs (username, entity, entity_uuid, action, changes, timestamp)
    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
    """
    await DataBase.execute(query, user_id, entity, entity_id, action, changes, datetime.now())
