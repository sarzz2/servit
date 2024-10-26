import argparse
import os
from typing import List

import asyncpg

from app.core.config import settings


async def create_migrations_table(pool):
    """
    Create the schema_migrations table to track applied migrations.
    """
    async with pool.acquire() as connection:
        await connection.execute(
            """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        )


async def get_applied_migrations(pool) -> List[str]:
    """
    Fetch the list of applied migrations from the schema_migrations table.
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT version FROM schema_migrations ORDER BY version;")
    return [row["version"] for row in rows]


async def record_migration(pool, version: str):
    """
    Record a migration as applied in the schema_migrations table.
    """
    async with pool.acquire() as connection:
        await connection.execute("INSERT INTO schema_migrations (version) VALUES ($1);", version)


async def remove_migration_record(pool, version: str):
    """
    Remove a migration record from the schema_migrations table.
    """
    async with pool.acquire() as connection:
        await connection.execute("DELETE FROM schema_migrations WHERE version = $1;", version)


async def run_migration(pool, filename: str, direction: str):
    """
    Run a migration script in the specified direction ('up' or 'down').
    """
    with open(filename, "r") as f:
        sql = f.read()

    # Split the file into 'up' and 'down' sections
    sections = sql.split("-- down")

    if direction == "up":
        sql_to_execute = sections[0].split("-- up")[1].strip()
    elif direction == "down":
        sql_to_execute = sections[1].strip() if len(sections) > 1 else ""
    else:
        raise ValueError("Invalid direction: choose 'up' or 'down'.")

    async with pool.acquire() as connection:
        await connection.execute(sql_to_execute)


async def apply_migrations(pool, direction: str = "up", steps: int = None):
    """
    Apply or rollback migrations up to a specific number of steps or to the latest state.
    """
    migrations_dir = os.path.join("app/models", "migrations")
    files = sorted(os.listdir(migrations_dir))

    applied_migrations = await get_applied_migrations(pool)

    if direction == "down":
        files = reversed(files)

    if steps is None:
        # Apply all pending migrations
        migrations_to_apply = [
            f
            for f in files
            if f.endswith(".sql") and (f not in applied_migrations if direction == "up" else f in applied_migrations)
        ]
    else:
        # Apply a specific number of steps
        migrations_to_apply = [
            f
            for f in files
            if f.endswith(".sql") and (f not in applied_migrations if direction == "up" else f in applied_migrations)
        ][:steps]

    for filename in migrations_to_apply:
        print(f"Running migration {direction}: {filename}")
        await run_migration(pool, os.path.join(migrations_dir, filename), direction)
        if direction == "up":
            await record_migration(pool, filename)
        elif direction == "down":
            await remove_migration_record(pool, filename)


async def run_specific_migration(pool, migration_name: str, direction: str = "up"):
    """
    Run a specific migration file in the specified direction.
    """
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    migration_path = os.path.join(migrations_dir, migration_name)

    if not os.path.exists(migration_path):
        raise FileNotFoundError(f"Migration {migration_name} does not exist.")

    if direction == "up":
        applied_migrations = await get_applied_migrations(pool)
        if migration_name in applied_migrations:
            print(f"Migration {migration_name} is already applied.")
            return
        await run_migration(pool, migration_path, "up")
        await record_migration(pool, migration_name)

    elif direction == "down":
        applied_migrations = await get_applied_migrations(pool)
        if migration_name not in applied_migrations:
            print(f"Migration {migration_name} is not applied and cannot be rolled back.")
            return
        await run_migration(pool, migration_path, "down")
        await remove_migration_record(pool, migration_name)


async def check_all_migrations_applied():
    migrations_dir = os.path.join("app/models", "migrations")
    files = sorted(os.listdir(migrations_dir))
    pool = await create_db_pool()
    try:
        applied_migration = await get_applied_migrations(pool)
    except asyncpg.UndefinedTableError:
        return False
    if applied_migration != files:
        return False
    return True


async def create_db_pool():
    return await asyncpg.create_pool(settings.DATABASE_URL)


async def main():
    parser = argparse.ArgumentParser(description="Manage database migrations.")
    parser.add_argument(
        "direction",
        nargs="?",
        default="up",
        choices=["up", "down"],
        help="Migration direction: 'up' to apply or 'down' to rollback (default: 'up').",
    )
    parser.add_argument(
        "steps",
        nargs="?",
        type=int,
        default=None,
        help="Number of steps to migrate up or down.",
    )
    parser.add_argument("--specific", "-s", type=str, help="Run a specific migration file.")

    args = parser.parse_args()

    db_pool = await create_db_pool()
    await create_migrations_table(db_pool)
    if args.specific:
        await run_specific_migration(db_pool, args.specific, direction=args.direction)
    else:
        await apply_migrations(db_pool, direction=args.direction, steps=args.steps)

    await db_pool.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
