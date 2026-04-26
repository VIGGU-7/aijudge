import os
from typing import Dict, Type, List
from app.schemas.ast_similarity import ASTAnalysis, ASTSimilarityResult
from app.services.ast_similarity.base import BaseASTParser
from app.services.ast_similarity.languages.python import PythonASTParser
from app.services.ast_similarity.languages.fallback import FallbackASTParser

class ASTSimilarityService:
    """
    Orchestrator for AST-based similarity analysis.
    Manages a registry of language-specific parsers.
    """

    def __init__(self):
        # Register language parsers by extension
        self._parsers: Dict[str, Type[BaseASTParser]] = {
            ".py": PythonASTParser,
            # Plug-ins for future:
            # ".js": JavaScriptASTParser,
            # ".ts": TypeScriptASTParser,
            # ".java": JavaASTParser,
            # ".cpp": CppASTParser,
        }
        self._fallback = FallbackASTParser()

    def get_parser(self, file_path: str) -> BaseASTParser:
        """
        Returns the appropriate parser for the file extension.
        """
        _, ext = os.path.splitext(file_path)
        parser_class = self._parsers.get(ext.lower())
        if parser_class:
            return parser_class()
        return self._fallback

    async def analyze_submission(self, files: Dict[str, str]) -> List[ASTAnalysis]:
        """
        Analyzes all files in a submission using the appropriate AST parsers.
        """
        analyses = []
        for path, content in files.items():
            parser = self.get_parser(path)
            analyses.append(parser.analyze(content, path))
        return analyses

    async def compare_submissions(self, source_analyses: List[ASTAnalysis], target_analyses: List[ASTAnalysis]) -> List[ASTSimilarityResult]:
        """
        Compares two sets of AST analyses.
        """
        results = []
        for s in source_analyses:
            for t in target_analyses:
                # Only compare if they are the same language (or both unsupported)
                if s.language == t.language:
                    parser = self._get_parser_for_language(s.language)
                    results.append(parser.calculate_similarity(s, t))
        return results

    def _get_parser_for_language(self, language: str) -> BaseASTParser:
        """
        Internal helper to get a parser instance by language name.
        """
        if language == "python":
            return PythonASTParser()
        return self._fallback
