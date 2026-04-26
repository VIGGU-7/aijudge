from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class FinalPlagiarismReport(BaseModel):
    """
    The final aggregated report for a suspicious submission pair.
    """
    submission_id_a: str
    submission_id_b: str
    
    # Aggregated Scores
    peer_plagiarism_percentage: float = Field(..., ge=0, le=100)
    ai_baseline_similarity_percentage: float = Field(..., ge=0, le=100)
    ai_likelihood_percentage: float = Field(..., ge=0, le=100)
    
    # Review Status
    final_review_risk: str # "high", "medium", "low", "minimal"
    review_reason_summary: str
    
    # Evidence from different layers
    evidence_highlights: List[str] = []
    
    # Raw component scores for transparency
    component_scores: Dict[str, float] = {}

class AggregatorConfig(BaseModel):
    """
    Configurable weights for the aggregation formula.
    """
    token_weight: float = 0.20
    ast_weight: float = 0.25
    skeleton_weight: float = 0.15
    embedding_weight: float = 0.10
    gemini_weight: float = 0.30
