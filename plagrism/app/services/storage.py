import logging
from typing import Protocol, BinaryIO, Dict, Any
from pathlib import Path
from google.cloud import storage
from app.core.config import settings

logger = logging.getLogger(__name__)

class IStorageService(Protocol):
    """
    Interface for cloud storage operations.
    """
    async def upload_file(self, content: BinaryIO, destination_path: str, content_type: str = "application/octet-stream") -> str: ...
    async def get_metadata(self, object_path: str) -> Dict[str, Any]: ...
    def generate_path(self, hackathon_id: str, team_id: str, submission_id: str, filename: str, is_raw: bool = True) -> str: ...

class GCStorageService:
    """
    Google Cloud Storage implementation.
    """
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(settings.STORAGE_BUCKET)

    def generate_path(
        self, 
        hackathon_id: str, 
        team_id: str, 
        submission_id: str, 
        filename: str, 
        is_raw: bool = True
    ) -> str:
        """
        Generates a deterministic path:
        submissions/{hackathon_id}/{team_id}/{submission_id}/{raw|processed}/{filename}
        """
        prefix = settings.RAW_PREFIX if is_raw else settings.PROCESSED_PREFIX
        return f"submissions/{hackathon_id}/{team_id}/{submission_id}/{prefix}/{filename}"

    async def upload_file(
        self, 
        content: BinaryIO, 
        destination_path: str, 
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Uploads a file to GCS and returns the full gs:// URI.
        """
        blob = self.bucket.blob(destination_path)
        
        # In actual async code, we'd use a thread pool or an async GCS lib like aio-gcs
        # but for this bootstrap we'll use the standard synchronous client.
        blob.upload_from_file(content, content_type=content_type)
        
        uri = f"gs://{settings.STORAGE_BUCKET}/{destination_path}"
        logger.info(f"Uploaded file to {uri}")
        return uri

    async def get_metadata(self, object_path: str) -> Dict[str, Any]:
        """
        Fetches metadata for an object in storage.
        """
        blob = self.bucket.get_blob(object_path)
        if not blob:
            raise FileNotFoundError(f"Object {object_path} not found in bucket {settings.STORAGE_BUCKET}")
            
        return {
            "size": blob.size,
            "content_type": blob.content_type,
            "updated": blob.updated,
            "md5_hash": blob.md5_hash,
        }

def get_storage_service() -> GCStorageService:
    return GCStorageService()
