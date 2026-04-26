import pytest
from app.services.similarity.fingerprint import CodeTokenizer, WinnowingFingerprinter

def test_tokenizer_anonymization():
    code = "def my_function(user_input):\n    result = user_input + 1\n    return result"
    tokens = CodeTokenizer.tokenize(code, anonymize=True)
    
    # Keywords should be preserved
    assert "def" in tokens
    assert "return" in tokens
    
    # Identifiers should be anonymized
    assert "my_function" not in tokens
    assert "ID" in tokens

def test_winnowing_invariance_to_renaming():
    fingerprinter = WinnowingFingerprinter(k=10, window_size=5)
    
    code_a = "def add(a, b): return a + b"
    code_b = "def sum(x, y): return x + y"
    
    fprints_a = fingerprinter.get_fingerprints(code_a)
    fprints_b = fingerprinter.get_fingerprints(code_b)
    
    # With anonymization (default), these should produce identical fingerprints
    assert fprints_a == fprints_b
