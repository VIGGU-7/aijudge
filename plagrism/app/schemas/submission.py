from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.enums import AnalysisStatus, SubmissionSource

class SubmissionBase(BaseModel):
    user_id: str
    project_id: str
    source_type: SubmissionSource
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission."""
    github_url: Optional[HttpUrl] = None
    # If direct upload, the frontend would provide the filename/etc here 
    # but the storage_uri is usually calculated by the backend after upload.

class SubmissionFileRead(BaseModel):
    file_path: str
    language: Optional[str]
    content_hash: str

class SubmissionRead(SubmissionBase):
    """Full submission data for response."""
    id: str
    storage_uri: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisJobRead(BaseModel):
    id: str
    submission_id: str
    status: AnalysisStatus
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubmissionWithFiles(SubmissionRead):
    files: List[SubmissionFileRead]
    analysis_jobs: List[AnalysisJobRead]
