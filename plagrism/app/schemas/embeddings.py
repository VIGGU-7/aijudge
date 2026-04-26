from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class EmbeddingChunk(BaseModel):
    """
    A single chunk of text to be embedded.
    """
    id: str
    text: str
    metadata: Dict[str, any] = {}

class EmbeddingRequest(BaseModel):
    """
    Request to generate embeddings for a list of chunks.
    """
    chunks: List[EmbeddingChunk]
    task_type: str = "RETRIEVAL_DOCUMENT" # Default for Vertex AI

class EmbeddingResponse(BaseModel):
    """
    Generated embeddings for the requested chunks.
    """
    vectors: List[List[float]]
    chunk_ids: List[str]
    model_name: str

class SemanticMatch(BaseModel):
    """
    Result of a semantic search.
    """
    id: str
    score: float # Cosine similarity (0.0 to 1.0)
    metadata: Dict[str, any] = {}
    text_snippet: Optional[str] = None

class MatchRetrievalResponse(BaseModel):
    """
    Aggregated semantic matches for a query.
    """
    query_id: str
    matches: List[SemanticMatch]
    total_matches: int
