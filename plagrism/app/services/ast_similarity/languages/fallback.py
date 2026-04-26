from app.services.ast_similarity.base import BaseASTParser
from app.schemas.ast_similarity import ASTAnalysis, ASTFingerprint, ASTSimilarityResult

class FallbackASTParser(BaseASTParser):
    """
    A graceful degradation parser for languages without a specific implementation.
    Does not perform actual AST parsing.
    """

    def analyze(self, content: str, file_path: str) -> ASTAnalysis:
        # Just provide some basic "fingerprint" based on text stats
        lines = content.splitlines()
        return ASTAnalysis(
            file_path=file_path,
            language="unsupported",
            fingerprint=ASTFingerprint(
                node_counts={"Lines": len(lines)},
                structure_hash=str(len(content)),
                max_depth=0
            ),
            is_fallback=True
        )

    def calculate_similarity(self, source: ASTAnalysis, target: ASTAnalysis) -> ASTSimilarityResult:
        return ASTSimilarityResult(
            source_id=source.file_path,
            target_id=target.file_path,
            structural_score=0.0,
            parser_confidence=0.0,
            structural_diff_summary="AST comparison not available for this language."
        )

    def get_parser_confidence(self) -> float:
        return 0.0
