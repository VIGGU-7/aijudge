import datetime
from typing import List, Dict, Type
from app.schemas.normalization import NormalizedFile, NormalizationResult, NormalizedBlock
from app.services.normalization.base import BaseNormalizer
from app.services.normalization.languages.python import PythonNormalizer
from app.services.normalization.languages.generic import GenericNormalizer

class NormalizationService:
    """
    Main service to handle code normalization for submissions.
    """
    
    def __init__(self):
        # Register language-specific normalizers
        self._normalizers: Dict[str, Type[BaseNormalizer]] = {
            ".py": PythonNormalizer,
            # Add more languages here as they are implemented
        }
        self._default_normalizer = GenericNormalizer

    def get_normalizer(self, file_path: str) -> BaseNormalizer:
        """
        Returns the appropriate normalizer instance based on file extension.
        """
        import os
        _, ext = os.path.splitext(file_path)
        normalizer_class = self._normalizers.get(ext.lower(), self._default_normalizer)
        return normalizer_class()

    async def normalize_submission(self, submission_id: str, files: Dict[str, str]) -> NormalizationResult:
        """
        Normalizes all files in a submission.
        
        Args:
            submission_id: The ID of the submission.
            files: A dictionary mapping file paths to their raw content.
        """
        normalized_files = []
        
        for path, content in files.items():
            normalizer = self.get_normalizer(path)
            
            # Normalize full content
            normalized_content = normalizer.normalize(content)
            content_hash = normalizer.calculate_hash(normalized_content)
            
            # Split into blocks
            blocks = normalizer.split_into_blocks(content)
            
            normalized_files.append(NormalizedFile(
                original_path=path,
                raw_content=content,
                normalized_content=normalized_content,
                language=self._get_language_name(path),
                content_hash=content_hash,
                line_count=len(content.splitlines()),
                blocks=blocks
            ))
            
        return NormalizationResult(
            submission_id=submission_id,
            files=normalized_files,
            total_files=len(normalized_files),
            normalization_timestamp=datetime.datetime.utcnow().isoformat()
        )

    def _get_language_name(self, file_path: str) -> str:
        import os
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c"
        }
        return mapping.get(ext, "unknown")
