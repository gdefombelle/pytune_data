import os
from minio import Minio
from pytune_configuration.sync_config_singleton import config, SimpleConfig

config = config or SimpleConfig()

MINIO_ENDPOINT = config.MINIO_ENDPOINT
MINIO_ACCESS_KEY = config.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = config.MINIO_SECRET_KEY
TEMP_BUCKET_NAME = config.MINIO_TEMP_BUCKET
PIANO_SESSION_BUCKET = config.MINIO_PIANO_SESSION_BUCKET

class MinioClient:
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False  # ⚠️ à adapter pour HTTPS plus tard
        )

    def ensure_bucket_exists(self):
        if not self.client.bucket_exists(TEMP_BUCKET_NAME):
            self.client.make_bucket(TEMP_BUCKET_NAME)

minio_client = MinioClient()
