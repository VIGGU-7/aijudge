import ast
import io
import tokenize
from typing import List
from app.services.normalization.base import BaseNormalizer
from app.schemas.normalization import NormalizedBlock

class PythonNormalizer(BaseNormalizer):
    """
    Python-specific normalizer that uses AST and tokenizer to remove docstrings, 
    comments, and normalize whitespace while preserving logical structure.
    """

    def normalize(self, content: str) -> str:
        """
        Removes comments and docstrings, then normalizes whitespace.
        """
        try:
            # 1. Remove comments using tokenize
            result = []
            g = tokenize.generate_tokens(io.StringIO(content).readline)
            for toknum, tokval, _, _, _ in g:
                if toknum != tokenize.COMMENT:
                    result.append((toknum, tokval))
            
            content_no_comments = tokenize.untokenize(result)
            
            # 2. Remove docstrings using AST
            tree = ast.parse(content_no_comments)
            
            class DocstringRemover(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    self.generic_visit(node)
                    if ast.get_docstring(node):
                        node.body = node.body[1:]
                    return node
                
                def visit_ClassDef(self, node):
                    self.generic_visit(node)
                    if ast.get_docstring(node):
                        node.body = node.body[1:]
                    return node
                
                def visit_Module(self, node):
                    self.generic_visit(node)
                    if ast.get_docstring(node):
                        node.body = node.body[1:]
                    return node

            tree = DocstringRemover().visit(tree)
            
            # 3. Unparse and normalize whitespace
            normalized = ast.unparse(tree)
            return self.strip_whitespace(normalized)
            
        except Exception:
            # Fallback to regex if parsing fails
            content = self.remove_comments_regex(content, single_line_prefix='#', 
                                              multi_line_start='"""', multi_line_end='"""')
            return self.strip_whitespace(content)

    def split_into_blocks(self, content: str) -> List[NormalizedBlock]:
        """
        Splits Python code into functions and classes.
        """
        blocks = []
        try:
            tree = ast.parse(content)
            lines = content.splitlines()
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line + len(ast.unparse(node).splitlines()))
                    
                    block_content = "\n".join(lines[start_line-1:end_line])
                    normalized_block_content = self.normalize(block_content)
                    
                    blocks.append(NormalizedBlock(
                        name=node.name,
                        block_type="function" if isinstance(node, ast.FunctionDef) else "class",
                        content=normalized_block_content,
                        start_line=start_line,
                        end_line=end_line,
                        content_hash=self.calculate_hash(normalized_block_content)
                    ))
            
            # If no blocks found, return the whole file
            if not blocks:
                return [
                    NormalizedBlock(
                        name="module",
                        block_type="module",
                        content=self.normalize(content),
                        start_line=1,
                        end_line=len(lines),
                        content_hash=self.calculate_hash(self.normalize(content))
                    )
                ]
                
            return blocks
        except Exception:
            return [
                NormalizedBlock(
                    name="failed_parse",
                    block_type="generic",
                    content=self.normalize(content),
                    start_line=1,
                    end_line=len(content.splitlines()),
                    content_hash=self.calculate_hash(self.normalize(content))
                )
            ]
