import ast
from typing import Dict, List, Set
from app.schemas.skeleton import SkeletonFingerprint

class SkeletonAnalyzer:
    """
    Extracts structural and stylometric fingerprints from source code.
    """

    @staticmethod
    def analyze_python(content: str, file_path: str = "unknown") -> SkeletonFingerprint:
        """
        Specific analyzer for Python code using AST.
        """
        try:
            tree = ast.parse(content)
        except Exception:
            return SkeletonFingerprint(language="python", line_count=len(content.splitlines()))

        # Tracking state
        stats = {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "control_flow": {},
            "nesting": 0,
            "max_nesting": 0,
            "import_modules": set(),
            "error_patterns": set()
        }

        class SkeletonVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                stats["functions"] += 1
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                stats["classes"] += 1
                self.generic_visit(node)

            def visit_Import(self, node):
                stats["imports"] += 1
                for alias in node.names:
                    stats["import_modules"].add(alias.name.split('.')[0])
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                stats["imports"] += 1
                if node.module:
                    stats["import_modules"].add(node.module.split('.')[0])
                self.generic_visit(node)

            def visit_Try(self, node):
                stats["control_flow"]["try"] = stats["control_flow"].get("try", 0) + 1
                stats["error_patterns"].add("try-except")
                self.generic_visit(node)

            def visit_If(self, node):
                stats["control_flow"]["if"] = stats["control_flow"].get("if", 0) + 1
                self.generic_visit(node)

            def visit_For(self, node):
                stats["control_flow"]["for"] = stats["control_flow"].get("for", 0) + 1
                self.generic_visit(node)

            def visit_While(self, node):
                stats["control_flow"]["while"] = stats["control_flow"].get("while", 0) + 1
                self.generic_visit(node)

            # Heuristic for nesting depth
            def visit(self, node):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.FunctionDef, ast.ClassDef)):
                    stats["nesting"] += 1
                    stats["max_nesting"] = max(stats["max_nesting"], stats["nesting"])
                    super().visit(node)
                    stats["nesting"] -= 1
                else:
                    super().visit(node)

        visitor = SkeletonVisitor()
        visitor.visit(tree)

        line_count = len(content.splitlines())
        # Helper-function decomposition ratio: functions per 100 lines
        decomp_ratio = (stats["functions"] / (line_count / 100.0)) if line_count > 0 else 0

        return SkeletonFingerprint(
            function_count=stats["functions"],
            class_count=stats["classes"],
            import_count=stats["imports"],
            max_nesting_depth=stats["max_nesting"],
            control_flow_counts=stats["control_flow"],
            decomposition_ratio=round(decomp_ratio, 2),
            error_handling_patterns=list(stats["error_patterns"]),
            import_modules=list(stats["import_modules"]),
            line_count=line_count,
            language="python"
        )
