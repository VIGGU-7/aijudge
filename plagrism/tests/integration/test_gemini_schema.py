import pytest
from app.schemas.gemini_analysis import PairwisePlagiarismReview

def test_gemini_response_validation():
    valid_json = {
        "semantic_similarity_percentage": 85.0,
        "shared_algorithmic_plan": "Both codes implement a binary search using a while loop.",
        "suspicious_transformations": [
            {"type": "variable_renaming", "description": "low/high renamed to start/end", "suspicion_level": "medium"}
        ],
        "evidence_summary": "Logic is identical line-by-line.",
        "confidence": 0.95,
        "manual_review_required": True,
        "verdict": "plagiarized"
    }
    
    review = PairwisePlagiarismReview.model_validate(valid_json)
    assert review.verdict == "plagiarized"
    assert len(review.suspicious_transformations) == 1

def test_gemini_response_invalid_score():
    invalid_json = {
        "semantic_similarity_percentage": 150.0, # Invalid > 100
        "shared_algorithmic_plan": "...",
        "suspicious_transformations": [],
        "evidence_summary": "...",
        "confidence": 0.95,
        "manual_review_required": False,
        "verdict": "clean"
    }
    
    with pytest.raises(Exception):
        PairwisePlagiarismReview.model_validate(invalid_json)
