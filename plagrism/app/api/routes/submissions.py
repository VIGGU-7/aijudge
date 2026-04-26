from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import Annotated
from app.schemas.submission import SubmissionRead, SubmissionWithFiles, SubmissionCreate
from app.services.submission import SubmissionService, get_submission_service

router = APIRouter()

@router.post("/upload/zip", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def upload_zip(
    file: UploadFile = File(...),
    user_id: Annotated[str, Form()] = ...,
    project_id: Annotated[str, Form()] = ...,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Upload a ZIP file containing project source code.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are supported"
        )
    
    return await service.create_from_zip(file, user_id, project_id)

@router.post("/github", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def submit_github(
    submission: SubmissionCreate,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Submit a GitHub repository URL for ingestion and analysis.
    """
    if not submission.github_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub URL is required for this endpoint"
        )
    
    return await service.create_from_github(
        str(submission.github_url), 
        submission.user_id, 
        submission.project_id
    )

@router.get("/{submission_id}", response_model=SubmissionWithFiles)
async def get_submission(
    submission_id: str,
    service: SubmissionService = Depends(get_submission_service)
):
    """
    Retrieve the status and files of a specific submission.
    """
    submission = await service.get_submission_status(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    return submission
