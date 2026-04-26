import ast
from typing import Dict, List, Set
from app.services.ast_similarity.base import BaseASTParser
from app.schemas.ast_similarity import ASTAnalysis, ASTFingerprint, ASTSimilarityResult

class PythonASTParser(BaseASTParser):
    """
    Concrete AST parser for Python using the built-in 'ast' module.
    """

    class StructureVisitor(ast.NodeVisitor):
        def __init__(self):
            self.node_types = []
            self.counts = {}
            self.max_depth = 0
            self.current_depth = 0
            self.complexity = 1 # Base complexity

        def visit(self, node):
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)
            
            node_type = type(node).__name__
            self.node_types.append(node_type)
            self.counts[node_type] = self.counts.get(node_type, 0) + 1
            
            # Estimate cyclomatic complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.And, ast.Or, ast.ExceptHandler)):
                self.complexity += 1
            
            super().visit(node)
            self.current_depth -= 1

    def analyze(self, content: str, file_path: str) -> ASTAnalysis:
        try:
            tree = ast.parse(content)
            visitor = self.StructureVisitor()
            visitor.visit(tree)
            
            fingerprint = ASTFingerprint(
                node_counts=visitor.counts,
                structure_hash=self.generate_structural_hash(visitor.node_types),
                max_depth=visitor.max_depth,
                cyclomatic_complexity=visitor.complexity
            )
            
            return ASTAnalysis(
                file_path=file_path,
                language="python",
                fingerprint=fingerprint,
                is_fallback=False
            )
        except Exception:
            # Return a degraded analysis if parsing fails
            return ASTAnalysis(
                file_path=file_path,
                language="python",
                fingerprint=ASTFingerprint(node_counts={}, structure_hash="failed", max_depth=0),
                is_fallback=True
            )

    def calculate_similarity(self, source: ASTAnalysis, target: ASTAnalysis) -> ASTSimilarityResult:
        """
        Calculates structural similarity between two Python ASTs.
        Uses weighted node count comparison and structural hash matching.
        """
        if source.is_fallback or target.is_fallback:
            return ASTSimilarityResult(
                source_id=source.file_path,
                target_id=target.file_path,
                structural_score=0.0,
                parser_confidence=0.5
            )

        # 1. Structural Hash Match (Exact topology match)
        if source.fingerprint.structure_hash == target.fingerprint.structure_hash:
            return ASTSimilarityResult(
                source_id=source.file_path,
                target_id=target.file_path,
                structural_score=100.0,
                parser_confidence=1.0,
                shared_structures=["Exact structural match (identical AST topology)"]
            )

        # 2. Vector-based comparison of node counts (Cosine similarity or similar)
        # For simplicity, we use a weighted intersection over union of node counts
        s_counts = source.fingerprint.node_counts
        t_counts = target.fingerprint.node_counts
        
        all_keys = set(s_counts.keys()).union(set(t_counts.keys()))
        intersection = 0
        union = 0
        
        # Weighting: Control structures matter more than expressions
        weights = {
            "For": 5, "While": 5, "If": 5, "FunctionDef": 10, "ClassDef": 15,
            "Return": 2, "Call": 2, "Assign": 1
        }
        
        for key in all_keys:
            weight = weights.get(key, 1)
            s_val = s_counts.get(key, 0)
            t_val = t_counts.get(key, 0)
            
            intersection += min(s_val, t_val) * weight
            union += max(s_val, t_val) * weight
            
        score = (intersection / union * 100) if union > 0 else 0
        
        return ASTSimilarityResult(
            source_id=source.file_path,
            target_id=target.file_path,
            structural_score=round(score, 2),
            parser_confidence=1.0,
            shared_structures=[f"Shared {k}: {min(s_counts.get(k, 0), t_counts.get(k, 0))}" 
                               for k in weights if k in s_counts and k in t_counts]
        )
