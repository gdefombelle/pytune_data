# db.py

from tortoise import Tortoise
from pytune_data.config_tortoise import get_orm_connection
from tortoise.exceptions import DBConnectionError
from pytune_data.config_tortoise import logger_admin

_initialized = False

async def init():
    global _initialized
    if not _initialized:
        try:
            # Initialiser Tortoise ORM
            await Tortoise.init(config=get_orm_connection())

            # Vérifier la connexion avec une requête simple
            connection = Tortoise.get_connection("default")
            await connection.execute_query("SELECT 1;")
            
            logger_admin.sync_log_info("Connection Tortoise to Postgres established successfully!")
            _initialized = True

        except DBConnectionError as e:
            logger_admin.sync_log_critical(f"Error: Tortoise was unable to connect to the database. Please check your DATABASE_URL: {e}")
        except Exception as e:
            logger_admin.sync_log_critical(f"An unexpected error occurred during Tortoise initialization: {e}")

async def close():
    global _initialized
    if _initialized:
        await Tortoise.close_connections()
        logger_admin.sync_log_info("Tortoise database connections closed.")
        _initialized = False

