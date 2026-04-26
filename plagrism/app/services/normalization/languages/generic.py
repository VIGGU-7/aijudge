from typing import List
from app.services.normalization.base import BaseNormalizer
from app.schemas.normalization import NormalizedBlock

class GenericNormalizer(BaseNormalizer):
    """
    A fallback normalizer that uses basic regex for comment removal and whitespace normalization.
    Suitable for languages without a specific normalizer.
    """
    
    def normalize(self, content: str) -> str:
        # Default to Python-style comments for generic if not specified
        content = self.remove_comments_regex(content)
        return self.strip_whitespace(content)

    def split_into_blocks(self, content: str) -> List[NormalizedBlock]:
        """
        Generic implementation just returns the whole file as one block.
        """
        return [
            NormalizedBlock(
                name="full_file",
                block_type="generic",
                content=self.normalize(content),
                start_line=1,
                end_line=len(content.splitlines()),
                content_hash=self.calculate_hash(content)
            )
        ]
