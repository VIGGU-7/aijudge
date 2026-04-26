from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class SuspiciousMatchSummary(BaseModel):
    """
    Summary of a suspicious match for the dashboard list view.
    """
    match_id: str
    target_submission_id: str
    target_user_handle: str
    similarity_score: float
    risk_level: str # "high", "medium", "low"
    primary_reason: str
    detected_at: datetime

class PlagiarismReportResponse(BaseModel):
    """
    Detailed report for a single submission.
    """
    submission_id: str
    overall_risk_score: float
    final_verdict: Optional[str] = None
    total_matches_found: int
    top_matches: List[SuspiciousMatchSummary]
    ai_likelihood_score: float
    review_recommendation: str

class EvidenceDetailResponse(BaseModel):
    """
    Deep-dive evidence for a specific pair of submissions.
    """
    match_id: str
    submission_id_a: str
    submission_id_b: str
    
    # Structural breakdown
    token_score: float
    ast_score: float
    skeleton_score: float
    semantic_score: float
    
    # Specific highlights
    evidence_highlights: List[str]
    shared_algorithmic_plan: Optional[str] = None
    
    # Comparison data
    code_a_snippet: str
    code_b_snippet: str

class ReviewerDecisionRequest(BaseModel):
    """
    Request to store a manual reviewer's decision.
    """
    verdict: str # "plagiarized", "suspicious", "clean"
    notes: str
    reviewer_id: str
    is_disqualified: bool = False

class RepoAnalysisRequest(BaseModel):
    """
    Request to analyze a remote repository.
    """
    repo_url: str
    challenge_id: Optional[str] = "remote_repo"
