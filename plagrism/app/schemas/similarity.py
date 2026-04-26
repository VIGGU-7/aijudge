from pydantic import BaseModel
from typing import List, Optional

class MatchDetail(BaseModel):
    """
    Details of a specific matching segment between two pieces of code.
    """
    source_chunk_id: Optional[str] = None
    target_chunk_id: Optional[str] = None
    similarity_score: float
    matched_tokens: int

class SimilarityScore(BaseModel):
    """
    The result of comparing two code entities (files or blocks).
    """
    source_id: str  # Path or name of source
    target_id: str  # Path or name of compared item
    score: float    # 0 to 100
    
    # Optional details for explanation
    matching_fingerprints_count: int
    total_fingerprints_source: int
    total_fingerprints_target: int
    
    match_details: List[MatchDetail] = []

    @property
    def percentage(self) -> float:
        """
        Returns the score as a percentage (0-100).
        """
        return self.score

class SimilarityReport(BaseModel):
    """
    Aggregated similarity report for a submission against a corpus.
    """
    submission_id: str
    top_matches: List[SimilarityScore]
    generated_at: str
    comparison_method: str = "winnowing_fingerprint"
