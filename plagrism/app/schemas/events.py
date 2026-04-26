from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.enums import SubmissionSource

class BaseEvent(BaseModel):
    """
    Base class for all system events to ensure consistent versioning and metadata.
    """
    version: str = "v1"
    timestamp: datetime = datetime.utcnow()
    event_id: Optional[str] = None # For tracking/deduplication

class SubmissionCreatedEvent(BaseEvent):
    """
    Event emitted when a new submission is received and stored.
    Triggers the plagiarism analysis pipeline.
    """
    submission_id: str
    hackathon_id: str
    team_id: str
    storage_uri: str
    source_type: SubmissionSource
    
    model_config = ConfigDict(use_enum_values=True)
