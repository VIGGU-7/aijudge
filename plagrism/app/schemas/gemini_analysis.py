from pydantic import BaseModel, Field
from typing import List, Optional

class PlagiarismTransformation(BaseModel):
    """
    Represents a specific modification made to the code to hide plagiarism.
    """
    type: str # e.g., "variable_renaming", "control_flow_flipping", "inline_functions"
    description: str
    suspicion_level: str # "high", "medium", "low"

class PairwisePlagiarismReview(BaseModel):
    """
    Structured output from Gemini for a pairwise plagiarism review.
    """
    semantic_similarity_percentage: float = Field(..., ge=0, le=100)
    shared_algorithmic_plan: str = Field(..., description="The core logic shared between the two pieces of code.")
    suspicious_transformations: List[PlagiarismTransformation]
    evidence_summary: str = Field(..., description="Detailed summary of the evidence found.")
    confidence: float = Field(..., ge=0, le=1)
    manual_review_required: bool
    
    verdict: str = Field(..., description="Final decision: 'plagiarized', 'suspicious', or 'clean'")

class GeminiAnalysisRequest(BaseModel):
    """
    Input for the Gemini analysis service.
    """
    submission_id_a: str
    submission_id_b: str
    code_a: str
    code_b: str
    language: str
    context: Optional[str] = None # e.g., "Both students belong to the same group"
