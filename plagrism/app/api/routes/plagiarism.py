from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.api.plagiarism import (
    PlagiarismReportResponse, 
    SuspiciousMatchSummary, 
    EvidenceDetailResponse, 
    ReviewerDecisionRequest,
    RepoAnalysisRequest
)
from app.services.plagiarism.review_service import PlagiarismReviewService
from app.services.ingestion.repo_service import RepoIngestionService

router = APIRouter(prefix="/plagiarism", tags=["plagiarism"])

# Dependencies
def get_review_service() -> PlagiarismReviewService:
    return PlagiarismReviewService()

def get_ingestion_service() -> RepoIngestionService:
    return RepoIngestionService()

@router.post("/analyze-repo")
async def analyze_remote_repo(
    request: RepoAnalysisRequest,
    service: RepoIngestionService = Depends(get_ingestion_service)
):
    """
    Downloads and analyzes a remote repository (e.g. GitHub) for plagiarism.
    """
    try:
        reports = await service.analyze_repo_url(request.repo_url)
        return {
            "status": "success",
            "matches_found": len(reports),
            "reports": reports
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports/{submission_id}", response_model=PlagiarismReportResponse)
async def get_plagiarism_report(
    submission_id: str, 
    service: PlagiarismReviewService = Depends(get_review_service)
):
    """
    Fetches the comprehensive plagiarism report for a specific submission.
    """
    try:
        return await service.get_report(submission_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/matches/top", response_model=List[SuspiciousMatchSummary])
async def get_top_matches(
    limit: int = 20, 
    challenge_id: Optional[str] = None,
    service: PlagiarismReviewService = Depends(get_review_service)
):
    """
    Returns a list of the most suspicious matches across the platform.
    """
    return await service.get_top_matches(limit=limit, challenge_id=challenge_id)

@router.get("/evidence/{match_id}", response_model=EvidenceDetailResponse)
async def get_match_evidence(
    match_id: str,
    service: PlagiarismReviewService = Depends(get_review_service)
):
    """
    Provides detailed evidence, including code snippets, for a specific match.
    """
    try:
        return await service.get_evidence(match_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Match evidence not found")

@router.post("/decisions/{match_id}")
async def submit_reviewer_decision(
    match_id: str, 
    request: ReviewerDecisionRequest,
    service: PlagiarismReviewService = Depends(get_review_service)
):
    """
    Records a reviewer's final verdict on a suspicious match.
    """
    success = await service.record_decision(match_id, request)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record decision")
    return {"status": "success"}
