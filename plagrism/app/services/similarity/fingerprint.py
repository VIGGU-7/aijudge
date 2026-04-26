import re
import hashlib
from typing import List, Set, Tuple

class CodeTokenizer:
    """
    Utility to tokenize code into a stream of significant symbols for similarity analysis.
    """
    
    # Simple regex to capture keywords, identifiers, and operators
    # This ignores whitespace and comments (which should already be removed by normalization)
    TOKEN_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+|[\+\-\*/%=\!<>&\^\|\~]+|[\(\)\[\]\{\},;]')

    # Keywords for common languages to preserve during anonymization
    KEYWORDS = {
        'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return', 'import', 'from', 'as', 'try', 'except', 'finally',
        'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'return', 'import', 'export', 'default'
    }

    @staticmethod
    def tokenize(content: str, anonymize: bool = True) -> List[str]:
        """
        Extracts tokens from code string.
        If anonymize is True, replaces identifiers (that aren't keywords) with 'ID'.
        """
        raw_tokens = CodeTokenizer.TOKEN_PATTERN.findall(content)
        if not anonymize:
            return raw_tokens
            
        processed_tokens = []
        for token in raw_tokens:
            if token[0].isalpha() or token[0] == '_':
                if token in CodeTokenizer.KEYWORDS:
                    processed_tokens.append(token)
                else:
                    processed_tokens.append('ID')
            else:
                processed_tokens.append(token)
        return processed_tokens

class WinnowingFingerprinter:
    """
    Implementation of the Winnowing algorithm for document fingerprinting.
    Reference: Schleimer et al. (2003) "Winnowing: Local Algorithms for Document Fingerprinting"
    """

    def __init__(self, k: int = 10, window_size: int = 4):
        """
        Args:
            k: The size of the k-grams (shingles). Larger k is more specific.
            window_size: The size of the sliding window for winnowing.
        """
        self.k = k
        self.window_size = window_size

    def get_fingerprints(self, content: str) -> Set[int]:
        """
        Generates a set of fingerprints for the given content.
        """
        tokens = CodeTokenizer.tokenize(content)
        if not tokens:
            return set()
            
        # Join tokens back into a dense string for k-gramming
        dense_content = "".join(tokens)
        
        if len(dense_content) < self.k:
            # Fallback for very short content
            return {int(hashlib.md5(dense_content.encode()).hexdigest()[:8], 16)}

        # 1. Generate k-grams and their hashes
        hashes = []
        for i in range(len(dense_content) - self.k + 1):
            kgram = dense_content[i:i + self.k]
            # Use first 8 characters of MD5 for a 32-bit integer hash
            h = int(hashlib.md5(kgram.encode()).hexdigest()[:8], 16)
            hashes.append(h)

        # 2. Winnowing
        fingerprints = set()
        if not hashes:
            return fingerprints

        # Sliding window of size w over the hashes
        for i in range(len(hashes) - self.window_size + 1):
            window = hashes[i:i + self.window_size]
            # Select the minimum hash in the window
            # If there are multiple identical minimums, the rightmost one is traditionally chosen
            min_hash = min(window)
            fingerprints.add(min_hash)
            
        return fingerprints

    @staticmethod
    def calculate_jaccard_similarity(set_a: Set[int], set_b: Set[int]) -> float:
        """
        Calculates Jaccard Similarity between two sets of fingerprints.
        Range: 0.0 to 1.0
        """
        if not set_a or not set_b:
            return 0.0
            
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        
        return intersection / union

    @staticmethod
    def calculate_containment_similarity(source_set: Set[int], target_set: Set[int]) -> float:
        """
        Calculates what percentage of the source set is present in the target set.
        Useful for detecting if a chunk of code was pasted into another file.
        """
        if not source_set:
            return 0.0
            
        intersection = len(source_set.intersection(target_set))
        return intersection / len(source_set)
