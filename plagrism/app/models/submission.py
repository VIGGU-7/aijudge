from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.models.enums import AnalysisStatus, SubmissionSource

class Base(DeclarativeBase):
    pass

class Submission(Base):
    """
    Represents a student's project submission for judging.
    """
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)  # Who submitted it
    project_id: Mapped[str] = mapped_column(String, index=True) # Which hackathon project
    
    source_type: Mapped[SubmissionSource] = mapped_column(SQLEnum(SubmissionSource))
    github_url: Mapped[Optional[str]] = mapped_column(String, nullable=True) # If via GitHub
    storage_uri: Mapped[Optional[str]] = mapped_column(String, nullable=True) # GCS path for zip/raw files
    
    metadata_: Mapped[dict] = mapped_column(JSON, default=dict) # Extra info (team names, tags, etc)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    files: Mapped[List["SubmissionFile"]] = relationship(back_populates="submission", cascade="all, delete-orphan")
    analysis_jobs: Mapped[List["AnalysisJob"]] = relationship(back_populates="submission")

class SubmissionFile(Base):
    """
    Individual source code files belonging to a submission.
    Used for granular plagiarism analysis.
    """
    __tablename__ = "submission_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    
    file_path: Mapped[str] = mapped_column(String) # path/to/file.py inside the project
    language: Mapped[Optional[str]] = mapped_column(String) # Detected language (Python, JS, etc)
    content_hash: Mapped[str] = mapped_column(String) # For quick duplicate detection
    gcs_uri: Mapped[str] = mapped_column(String) # Where the specific file is stored
    
    submission: Mapped["Submission"] = relationship(back_populates="files")

class AnalysisJob(Base):
    """
    Tracks the lifecycle of a plagiarism analysis run.
    Connects to Pub/Sub events.
    """
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"))
    
    status: Mapped[AnalysisStatus] = mapped_column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results metadata (score, matched documents, etc)
    results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    submission: Mapped["Submission"] = relationship(back_populates="analysis_jobs")
