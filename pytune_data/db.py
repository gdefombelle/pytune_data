# db.py

from tortoise import Tortoise
from pytune_data.config_tortoise import get_orm_connection
from tortoise.exceptions import DBConnectionError
from simple_logger.logger import get_logger, SimpleLogger
from functools import wraps

_initialized = False

logger : SimpleLogger = get_logger("data")

async def init():
    global _initialized
    if not _initialized:
        try:
            # Initialiser Tortoise ORM
            await Tortoise.init(config=get_orm_connection())
            # await Tortoise.generate_schemas() <-- EN DEV UNIQUEMENT 
            # Vérifier la connexion avec une requête simple
            connection = Tortoise.get_connection("default")
            await connection.execute_query("SELECT 1;")
            
            await logger.ainfo("Connection Tortoise to Postgres established successfully!")
            _initialized = True

        except DBConnectionError as e:
            await logger.acritical(f"Error: Tortoise was unable to connect to the database. Please check your DATABASE_URL: {e}")
        except Exception as e:
            await logger.acritical(f"An unexpected error occurred during Tortoise initialization: {e}")

async def close():
    global _initialized
    if _initialized:
        await Tortoise.close_connections()
        await logger.ainfo("Tortoise database connections closed.")
        _initialized = False


def ensure_db_initialized(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await init()
        return await func(*args, **kwargs)
    return wrapper
