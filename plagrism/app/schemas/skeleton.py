from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class SkeletonFingerprint(BaseModel):
    """
    Captures structural and stylometric signals of a code entity.
    """
    # Robust counts
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    
    # Structural signals
    max_nesting_depth: int = 0
    control_flow_counts: Dict[str, int] = Field(default_factory=dict) # e.g. {"if": 5, "try": 2}
    
    # Stylometric / Heuristic signals
    decomposition_ratio: float = 0.0 # Ratio of helper functions to total lines (or classes)
    error_handling_patterns: List[str] = [] # Types of error handling used (e.g. "try-except", "result-type")
    import_modules: List[str] = [] # List of imported top-level modules
    
    # Metadata
    line_count: int = 0
    language: str = "unknown"

class SkeletonSimilarityScore(BaseModel):
    """
    Result of comparing two skeleton fingerprints.
    """
    source_id: str
    target_id: str
    overall_score: float # 0 to 100
    
    # Component scores (0 to 1)
    structural_match: float
    stylometric_match: float
    complexity_match: float
    
    matches: List[str] = []
