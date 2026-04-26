from pydantic import BaseModel, Field
from typing import List, Optional

class AILikelihoodReport(BaseModel):
    """
    HEURISTIC ESTIMATE of whether a submission is AI-generated.
    
    WARNING: This is an estimation based on patterns and should NOT be used 
    as definitive proof of academic dishonesty. AI detection is inherently 
    uncertain and prone to false positives.
    """
    ai_likelihood_percentage: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    
    reasons: List[str] = Field(..., description="List of patterns that suggest AI or human origin.")
    limitations: List[str] = Field(..., description="Factors that may have reduced the accuracy of this estimate.")
    
    # Stylometric signals found
    signals: List[str] = []

class AIDetectionRequest(BaseModel):
    """
    Input for the AI likelihood analysis service.
    """
    submission_id: str
    code: str
    language: str
    skeleton_data: Optional[dict] = None
    similarity_context: Optional[str] = None
