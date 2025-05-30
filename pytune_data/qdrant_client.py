import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from pytune_configuration.sync_config_singleton import config, SimpleConfig

config = config or SimpleConfig()

QDRANT_HOST = config.QDRANT_HOST
QDRANT_PORT = config.QDRANT_PORT
COLLECTION_NAME = config.QDRANT_COLLECTION_NAME

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def ensure_collection_exists():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=128, distance=Distance.COSINE),
        )
