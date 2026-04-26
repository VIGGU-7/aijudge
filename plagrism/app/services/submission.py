from typing import Protocol, Optional
from fastapi import UploadFile
from datetime import datetime
import uuid

from app.schemas.submission import SubmissionRead, SubmissionWithFiles, SubmissionCreate
from app.schemas.events import SubmissionCreatedEvent
from app.models.enums import SubmissionSource
from app.services.pubsub import GcpPublisherService, get_publisher_service

class ISubmissionService(Protocol):
    async def create_from_zip(self, file: UploadFile, user_id: str, hackathon_id: str, team_id: str) -> SubmissionRead: ...
    async def create_from_github(self, github_url: str, user_id: str, hackathon_id: str, team_id: str) -> SubmissionRead: ...

class SubmissionService:
    def __init__(self, publisher: GcpPublisherService = None):
        # In a real app, this would be injected via FastAPI Depends
        self.publisher = publisher or get_publisher_service()

    async def create_from_zip(self, file: UploadFile, user_id: str, hackathon_id: str, team_id: str) -> SubmissionRead:
        submission_id = str(uuid.uuid4())
        storage_uri = f"gs://bucket/raw/{submission_id}.zip" # This would come from storage service
        
        # 1. Store in DB (Stub)
        submission = SubmissionRead(
            id=submission_id,
            user_id=user_id,
            project_id=hackathon_id,
            source_type=SubmissionSource.ZIP_UPLOAD,
            created_at=datetime.utcnow()
        )
        
        # 2. Publish Event
        event = SubmissionCreatedEvent(
            submission_id=submission_id,
            hackathon_id=hackathon_id,
            team_id=team_id,
            storage_uri=storage_uri,
            source_type=SubmissionSource.ZIP_UPLOAD
        )
        await self.publisher.publish_submission_created(event)
        
        return submission

    async def create_from_github(self, github_url: str, user_id: str, hackathon_id: str, team_id: str) -> SubmissionRead:
        submission_id = str(uuid.uuid4())
        
        submission = SubmissionRead(
            id=submission_id,
            user_id=user_id,
            project_id=hackathon_id,
            source_type=SubmissionSource.GITHUB_REPO,
            created_at=datetime.utcnow()
        )
        
        event = SubmissionCreatedEvent(
            submission_id=submission_id,
            hackathon_id=hackathon_id,
            team_id=team_id,
            storage_uri=github_url, # For GitHub, the "storage" is the URL itself initially
            source_type=SubmissionSource.GITHUB_REPO
        )
        await self.publisher.publish_submission_created(event)
        
        return submission

    async def get_submission_status(self, submission_id: str) -> Optional[SubmissionWithFiles]:
        return None

def get_submission_service() -> SubmissionService:
    return SubmissionService()
