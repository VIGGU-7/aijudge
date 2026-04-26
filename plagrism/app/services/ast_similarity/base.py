from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.ast_similarity import ASTAnalysis, ASTSimilarityResult, ASTFingerprint

class BaseASTParser(ABC):
    """
    Abstract base class for language-specific AST parsers.
    """
    
    @abstractmethod
    def analyze(self, content: str, file_path: str) -> ASTAnalysis:
        """
        Parses the code and returns a structural analysis.
        """
        pass

    @abstractmethod
    def calculate_similarity(self, source: ASTAnalysis, target: ASTAnalysis) -> ASTSimilarityResult:
        """
        Compares two AST analyses and returns a similarity score.
        """
        pass

    def get_parser_confidence(self) -> float:
        """
        Returns the confidence level of this parser (default 1.0).
        Can be overridden if a parser is experimental or partial.
        """
        return 1.0

    def generate_structural_hash(self, nodes: List[str]) -> str:
        """
        Helper to generate a deterministic hash from a sequence of node types.
        """
        import hashlib
        content = ",".join(nodes)
        return hashlib.sha256(content.encode()).hexdigest()
