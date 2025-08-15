from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4
from pytune_data import minio_client, PIANO_SESSION_IMAGES_BUCKET
from pytune_helpers.image_bytes import _sniff_mime_ext, coerce_to_image_bytes


def upload_generated_image_bytes(raw: object, session_id: str) -> str:
    """
    Conformité MinIO: client.put_object(bucket, fname, stream, length=..., content_type=...).
    Retourne l’URL publique.
    """
    img_bytes = coerce_to_image_bytes(raw)
    mime, ext = _sniff_mime_ext(img_bytes)

    fname = f"piano-beautify/{session_id}/{uuid4().hex}.{ext}"
    buf = BytesIO(img_bytes)            # <- objet fichier comme dans ton code
    length = buf.getbuffer().nbytes     # <- même pattern que pour 'compressed'

    minio_client.client.put_object(
        PIANO_SESSION_IMAGES_BUCKET,
        fname,
        buf,
        length=length,
        content_type=mime
    )

    return f"https://minio.pytune.com/{PIANO_SESSION_IMAGES_BUCKET}/{fname}"

def download_from_minio(bucket: str, object_name: str) -> bytes:
    """
    Télécharge un objet MinIO et retourne son contenu en bytes.
    """
    try:
        response = minio_client.client.get_object(bucket, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to download {object_name} from {bucket}: {e}")

def download_from_minio_url(minio_url: str) -> bytes:
    """
    Parse l'URL complète et télécharge le fichier depuis MinIO.
    Exemple: https://minio.pytune.com/piano-identification-sessions/identify_xxx.jpg
    """
    parsed = urlparse(minio_url)
    parts = parsed.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid MinIO URL: {minio_url}")
    bucket, object_name = parts
    return download_from_minio(bucket, object_name)