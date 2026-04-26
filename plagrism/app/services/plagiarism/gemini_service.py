import os
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.schemas.gemini_analysis import PairwisePlagiarismReview, GeminiAnalysisRequest

class GeminiAnalysisService:
    """
    Service for performing deep plagiarism analysis using Gemini 1.5 Flash/Pro.
    
    ARCHITECTURE NOTE:
    This service should be invoked by background workers (e.g., Celery or Pub/Sub handlers),
    NOT directly from the API routes. LLM analysis is high-latency and expensive; 
    shortlisting should always happen first.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash-001"):
        self.model_name = model_name
        self._model = None
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "../../prompts/plagiarism_review.txt")
        with open(prompt_path, "r") as f:
            return f.read()

    async def review_pair(self, request: GeminiAnalysisRequest) -> PairwisePlagiarismReview:
        """
        Submits a pair of code submissions to Gemini for a structured review.
        """
        if not self._model:
            self._model = GenerativeModel(self.model_name)

        prompt = self._prompt_template.format(
            language=request.language,
            code_a=request.code_a,
            code_b=request.code_b
        )

        # Configure structured output using the Pydantic schema
        # Note: Response schema support depends on the specific SDK version and model capabilities
        response = await self._model.generate_content_async(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=PairwisePlagiarismReview.model_json_schema()
            )
        )

        # Parse the JSON response back into the Pydantic model
        return PairwisePlagiarismReview.model_validate_json(response.text)
