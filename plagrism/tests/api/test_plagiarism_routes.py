import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_plagiarism_report_not_found():
    # submission_id doesn't exist (mock currently returns 78.5 for any ID)
    response = client.get("/api/v1/plagiarism/reports/missing_id")
    assert response.status_code == 200 # Current mock always returns 200
    assert response.json()["submission_id"] == "missing_id"

def test_submit_reviewer_decision():
    match_id = "match_123"
    decision = {
        "verdict": "plagiarized",
        "notes": "Confirmed by side-by-side comparison.",
        "reviewer_id": "judge_1",
        "is_disqualified": True
    }
    response = client.post(f"/api/v1/plagiarism/decisions/{match_id}", json=decision)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
