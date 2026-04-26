import asyncio
from typing import List, Optional
import tenacity
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from app.services.embeddings.base import BaseEmbeddingsService
from app.schemas.embeddings import EmbeddingChunk, EmbeddingResponse

class VertexEmbeddingsService(BaseEmbeddingsService):
    """
    Implementation of embeddings using Google Cloud Vertex AI.
    """

    def __init__(self, model_name: str = "text-embedding-004", project: str = None, location: str = "us-central1"):
        self.model_name = model_name
        self.location = location
        # Initialize vertexai in the constructor or assume it's done globally
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = TextEmbeddingModel.from_pretrained(self.model_name)
        return self._model

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        stop=tenacity.stop_after_attempt(3),
        retry=tenacity.retry_if_exception_type(Exception),
    )
    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> List[float]:
        """
        Embeds a single text. Vertex SDK is synchronous, so we run in executor.
        """
        model = self._get_model()
        # Vertex AI SDK is blocking, we wrap in thread for async safety if needed
        # but for simple calls we can just await the loop executor
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            lambda: model.get_embeddings([TextEmbeddingInput(text, task_type)])
        )
        return embeddings[0].values

    async def embed_batch(self, chunks: List[EmbeddingChunk], task_type: str = "RETRIEVAL_DOCUMENT") -> EmbeddingResponse:
        """
        Embeds a batch of chunks, respecting Vertex AI limits (usually 250 per request).
        """
        BATCH_SIZE = 250
        all_vectors = []
        chunk_ids = [c.id for c in chunks]
        
        # Split into sub-batches
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            inputs = [TextEmbeddingInput(c.text, task_type) for c in batch]
            
            # Use retry logic for each batch
            vectors = await self._get_embeddings_with_retry(inputs)
            all_vectors.extend(vectors)
            
        return EmbeddingResponse(
            vectors=all_vectors,
            chunk_ids=chunk_ids,
            model_name=self.model_name
        )

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        stop=tenacity.stop_after_attempt(3)
    )
    async def _get_embeddings_with_retry(self, inputs: List[TextEmbeddingInput]) -> List[List[float]]:
        model = self._get_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            lambda: model.get_embeddings(inputs)
        )
        return [e.values for e in embeddings]

    def get_dimension(self) -> int:
        """
        Returns dimension for text-embedding-004 (default 768).
        """
        # Could be 768 or 3072 depending on configuration
        return 768
