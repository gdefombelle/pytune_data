from minio import Minio
from pytune_configuration.sync_config_singleton import config, SimpleConfig

config = config or SimpleConfig()

MINIO_ENDPOINT = config.MINIO_ENDPOINT  # "minio:9000"
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
            secure=False,
            region="us-east-1"  # 👈 supprime le warning location=
        )

    def ensure_bucket_exists(self):
        if not self.client.bucket_exists(TEMP_BUCKET_NAME):
            self.client.make_bucket(TEMP_BUCKET_NAME)

minio_client = MinioClient()