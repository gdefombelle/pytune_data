# model/config.py
import os
import asyncio
from simple_logger.logger import get_logger, SimpleLogger
from pytune_configuration.sync_config_singleton import config, SimpleConfig

if config is None:
    config = SimpleConfig()

logger : SimpleLogger = get_logger("data")

DATABASE_URL = None
TORTOISE_ORM_CONNECTION = None

def get_database_url()-> str:
    global DATABASE_URL
    DATABASE_URL = f"postgres://{os.getenv("FASTAPI_USER")}:{os.getenv("FASTAPI_PWD")}@{os.getenv("DB_HOST")}:{config.DB_PORT}/{config.DB_NAME}"
    return DATABASE_URL

def get_orm_connection():
    """Construit et renvoie la configuration de Tortoise ORM."""
    global TORTOISE_ORM_CONNECTION
    TORTOISE_ORM_CONNECTION =  {
        "connections": {"default": get_database_url()},
        "apps": {
            "models": {
                "models": ["pytune_data.models"],
                "default_connection": "default",
            }
        },
    }
    return TORTOISE_ORM_CONNECTION


