import pytest
from app.services.normalization.languages.python import PythonNormalizer

@pytest.fixture
def python_normalizer():
    return PythonNormalizer()

def test_python_normalization_strips_comments(python_normalizer):
    code = "x = 1 # This is a comment\n# Full line comment\ny = 2"
    normalized = python_normalizer.normalize(code)
    assert "#" not in normalized
    assert "x = 1" in normalized
    assert "y = 2" in normalized

def test_python_normalization_strips_docstrings(python_normalizer):
    code = '"""Module docstring"""\ndef foo():\n    """Function docstring"""\n    return 42'
    normalized = python_normalizer.normalize(code)
    assert "Module docstring" not in normalized
    assert "Function docstring" not in normalized
    assert "return 42" in normalized

def test_python_normalization_deterministic(python_normalizer):
    code = "def foo():\n    return 1"
    norm1 = python_normalizer.normalize(code)
    norm2 = python_normalizer.normalize(code)
    assert norm1 == norm2
