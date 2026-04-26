from pydantic import BaseModel
from typing import List, Optional

class NormalizedBlock(BaseModel):
    """
    Represents a logical block of code (e.g., a function or class).
    """
    name: str
    block_type: str  # e.g., 'function', 'class', 'generic'
    content: str
    start_line: int
    end_line: int
    content_hash: str

class NormalizedFile(BaseModel):
    """
    Represents the output of the normalization process for a single file.
    """
    original_path: str
    raw_content: str
    normalized_content: str
    language: str
    content_hash: str
    line_count: int
    blocks: List[NormalizedBlock] = []

class NormalizationResult(BaseModel):
    """
    Container for all normalized files in a submission.
    """
    submission_id: str
    files: List[NormalizedFile]
    total_files: int
    normalization_timestamp: str
