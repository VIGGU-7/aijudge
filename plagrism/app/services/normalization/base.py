from abc import ABC, abstractmethod
import hashlib

from typing import List
from app.schemas.normalization import NormalizedBlock

class BaseNormalizer(ABC):
    """
    Abstract base class for language-specific code normalizers.
    """
    
    @abstractmethod
    def normalize(self, content: str) -> str:
        """
        Takes raw source code and returns normalized version for comparison.
        """
        pass

    @abstractmethod
    def split_into_blocks(self, content: str) -> List[NormalizedBlock]:
        """
        Splits the code into logical blocks (functions, classes).
        """
        pass

    def calculate_hash(self, content: str) -> str:
        """
        Deterministic hash of the normalized content.
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def strip_whitespace(self, content: str) -> str:
        """
        Collapses multiple spaces/newlines into single ones to ignore formatting differences.
        """
        import re
        # Remove empty lines
        content = re.sub(r'^\s*$\n', '', content, flags=re.MULTILINE)
        # Collapse multiple spaces and tabs to a single space
        content = re.sub(r'[ \t]+', ' ', content)
        # Ensure only single newlines
        content = re.sub(r'\n+', '\n', content)
        return content.strip()

    def remove_comments_regex(self, content: str, single_line_prefix: str = '#', 
                             multi_line_start: str = None, multi_line_end: str = None) -> str:
        """
        Generic regex-based comment removal.
        """
        import re
        
        # Multi-line comments
        if multi_line_start and multi_line_end:
            pattern = re.escape(multi_line_start) + r'.*?' + re.escape(multi_line_end)
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            
        # Single-line comments
        pattern = re.escape(single_line_prefix) + r'.*$'
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        return content
