import asyncio
from app.services.normalization.service import NormalizationService
from app.services.similarity.fingerprint import WinnowingFingerprinter
from app.services.ast_similarity.service import ASTSimilarityService
from app.services.similarity.skeleton.analyzer import SkeletonAnalyzer
from app.services.plagiarism.aggregator import ScoringAggregator

async def run_full_pipeline_demo():
    print("Initializing AIJudge Plagiarism Engine v1.0...")
    
    # 1. Setup Services
    norm_service = NormalizationService()
    ast_service = ASTSimilarityService()
    skeleton_analyzer = SkeletonAnalyzer()
    aggregator = ScoringAggregator()
    
    # 2. Input Code
    code_a = """
def process_orders(orders):
    \"\"\"Calculates total with tax.\"\"\"
    total = 0
    for order in orders:
        if order.status == 'valid':
            total += order.price * 1.15
    return total
"""
    
    code_b = """
def get_final_amount(data):
    # Logic to get total
    res = 0
    for item in data:
        if item.status == 'valid':
            # Add 15% tax
            res = res + (item.price * 1.15)
    return res
"""

    print("\n[1/4] Normalizing Code...")
    norm_a = await norm_service.normalize_submission("sub_a", {"main.py": code_a})
    norm_b = await norm_service.normalize_submission("sub_b", {"main.py": code_b})
    
    # 3. Token Similarity (Winnowing)
    print("[2/4] Running Token Fingerprinting...")
    fprinter = WinnowingFingerprinter(k=10, window_size=5)
    fprints_a = fprinter.get_fingerprints(norm_a.files[0].normalized_content)
    fprints_b = fprinter.get_fingerprints(norm_b.files[0].normalized_content)
    token_score = round(fprinter.calculate_jaccard_similarity(fprints_a, fprints_b) * 100, 2)
    
    # 4. AST Similarity
    print("[3/4] Analyzing AST Structures...")
    ast_a = await ast_service.analyze_submission({"main.py": code_a})
    ast_b = await ast_service.analyze_submission({"main.py": code_b})
    ast_results = await ast_service.compare_submissions(ast_a, ast_b)
    ast_score = ast_results[0].structural_score
    
    # 5. Skeleton/Stylometry
    print("[4/4] Extracting Stylometric Skeleton...")
    skel_a = skeleton_analyzer.analyze_python(code_a)
    skel_b = skeleton_analyzer.analyze_python(code_b)
    
    # 6. Final Aggregation
    print("\n--- FINAL PLAGIARISM REPORT ---")
    report = await aggregator.aggregate(
        token_score=token_score,
        ast_score=ast_score,
        skeleton_score=85.0, # Mocked
        embedding_score=60.0, # Mocked
        gemini_score=90.0,    # Mocked
        ai_likelihood=10.0,
        meta_data={"id_a": "sub_a", "id_b": "sub_b"}
    )
    
    print(f"Peer Plagiarism Score: {report.peer_plagiarism_percentage}%")
    print(f"Risk Level: {report.final_review_risk.upper()}")
    print(f"Summary: {report.review_reason_summary}")
    print("\nEvidence Highlights:")
    for h in report.evidence_highlights:
        print(f" - {h}")

if __name__ == "__main__":
    asyncio.run(run_full_pipeline_demo())
