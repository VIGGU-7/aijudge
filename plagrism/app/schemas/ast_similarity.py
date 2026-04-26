from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class ASTNodeStructure(BaseModel):
    """
    Simplified representation of an AST node for structural comparison.
    """
    node_type: str
    children_types: List[str]
    depth: int
    complexity_score: float = 1.0

class ASTFingerprint(BaseModel):
    """
    A language-agnostic structural fingerprint of a code block.
    """
    node_counts: Dict[str, int]  # e.g., {"FunctionDef": 2, "For": 5}
    structure_hash: str          # Hash of the tree structure (topology)
    max_depth: int
    cyclomatic_complexity: Optional[int] = None
    significant_subtrees: List[str] = [] # Hashes of important subtrees

class ASTSimilarityResult(BaseModel):
    """
    Detailed result of comparing two ASTs.
    """
    source_id: str
    target_id: str
    structural_score: float = Field(..., ge=0, le=100)
    parser_confidence: float = Field(..., ge=0, le=1) # 1.0 = full AST, 0.5 = partial, etc.
    
    # Hints for explaining the match
    shared_structures: List[str] = []
    structural_diff_summary: Optional[str] = None
    
    metadata: Dict[str, Any] = {}

class ASTAnalysis(BaseModel):
    """
    Result of an AST analysis for a single file/block.
    """
    file_path: str
    language: str
    fingerprint: ASTFingerprint
    is_fallback: bool = False
