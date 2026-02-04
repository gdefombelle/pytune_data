from minio import Minio
from pytune_configuration.sync_config_singleton import config, SimpleConfig
import os

config = config or SimpleConfig()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT") or config.MINIO_ENDPOINT
MINIO_SECURE = os.getenv("MINIO_SECURE")

if MINIO_SECURE is not None:
    MINIO_SECURE = MINIO_SECURE.lower() in ("1", "true", "yes", "on")
else:
    MINIO_SECURE = bool(config.MINIO_SECURE)

MINIO_ACCESS_KEY = config.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = config.MINIO_SECRET_KEY

TEMP_BUCKET_NAME = config.MINIO_TEMP_BUCKET
PIANO_SESSION_IMAGES_BUCKET = config.PIANO_SESSION_IMAGES_BUCKET
PIANO_SESSIONS_PDF_BUCKET = config.PIANO_SESSIONS_PDF_BUCKET


class MinioClient:
    def __init__(self):
        endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")

        self.client = Minio(
            endpoint,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE, # type: ignore
            region="us-east-1"
        )

    def ensure_bucket_exists(self):
        if not self.client.bucket_exists(TEMP_BUCKET_NAME):
            self.client.make_bucket(TEMP_BUCKET_NAME)


minio_client = MinioClient()