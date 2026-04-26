from fastapi import APIRouter
from datetime import datetime
from app.api.routes import submissions
from app.schemas.submission import SubmissionWithFiles
from app.models.enums import AnalysisStatus, SubmissionSource

api_router = APIRouter()

@api_router.get("/health", tags=["system"])
async def health_check():
    """
    Standard health check endpoint.
    Used by Cloud Run for liveness and readiness probes.
    """
    return {
        "status": "online",
        "service": "ai-judge-plagiarism",
        "version": "1.0.0"
    }

@api_router.get("/debug/submission", response_model=SubmissionWithFiles, tags=["debug"])
async def debug_submission():
    """
    Placeholder endpoint to verify that schemas and enums are working correctly.
    """
    return {
        "id": "sub_123",
        "user_id": "user_456",
        "project_id": "proj_789",
        "source_type": SubmissionSource.ZIP_UPLOAD,
        "metadata": {"team": "Antigravity"},
        "storage_uri": "gs://bucket/sub_123.zip",
        "created_at": datetime.utcnow(),
        "files": [
            {"file_path": "main.py", "language": "python", "content_hash": "abc"}
        ],
        "analysis_jobs": [
            {
                "id": "job_1",
                "submission_id": "sub_123",
                "status": AnalysisStatus.PENDING
            }
        ]
    }

# Intake Routes
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])

# Plagiarism Analysis Routes
from app.api.routes import plagiarism
api_router.include_router(plagiarism.router)
