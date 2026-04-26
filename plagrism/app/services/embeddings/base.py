from abc import ABC, abstractmethod
from typing import List, Dict
from app.schemas.embeddings import EmbeddingChunk, EmbeddingResponse

class BaseEmbeddingsService(ABC):
    """
    Abstract interface for embedding generation services.
    """

    @abstractmethod
    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> List[float]:
        """
        Generates an embedding for a single text string.
        """
        pass

    @abstractmethod
    async def embed_batch(self, chunks: List[EmbeddingChunk], task_type: str = "RETRIEVAL_DOCUMENT") -> EmbeddingResponse:
        """
        Generates embeddings for a batch of text chunks.
        Should handle batching internally based on provider limits.
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Returns the dimension of the embedding vectors produced by this service.
        """
        pass
