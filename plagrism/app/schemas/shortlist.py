from pydantic import BaseModel
from typing import List, Dict, Set, Optional

class ShortlistedPair(BaseModel):
    """
    A pair of submissions flagged for deeper plagiarism analysis.
    """
    submission_id_a: str
    submission_id_b: str
    
    # Fast metrics used for shortlisting
    token_collision_count: int
    skeleton_similarity_score: float
    
    # Aggregated priority for ordering (0-100)
    priority_score: float
    
    # Reasons for shortlisting
    reasons: List[str]
    
    # Context for downstream services
    challenge_id: str
    language: str

class ShortlistReport(BaseModel):
    """
    The output of the candidate shortlisting phase.
    """
    challenge_id: str
    total_candidates_processed: int
    shortlisted_pairs: List[ShortlistedPair]
    generated_at: str
