from enum import Enum

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SubmissionSource(str, Enum):
    ZIP_UPLOAD = "zip_upload"
    GITHUB_REPO = "github_repo"
    DIRECT_UPLOAD = "direct_upload"
