import asyncio
from typing import List, Dict
from app.services.normalization.service import NormalizationService
from app.services.similarity.shortlist import ShortlistingService
from app.services.similarity.fingerprint import WinnowingFingerprinter
from app.services.ast_similarity.service import ASTSimilarityService
from app.services.similarity.skeleton.analyzer import SkeletonAnalyzer
from app.services.plagiarism.aggregator import ScoringAggregator
from app.schemas.final_report import FinalPlagiarismReport

class PlagiarismOrchestrator:
    """
    Orchestrates the entire plagiarism detection pipeline for a batch of submissions.
    """

    def __init__(self):
        self.norm_service = NormalizationService()
        self.shortlisting_service = ShortlistingService()
        self.ast_service = ASTSimilarityService()
        self.skeleton_analyzer = SkeletonAnalyzer()
        self.aggregator = ScoringAggregator()
        self.fprinter = WinnowingFingerprinter(k=10, window_size=5)

    async def run_batch_analysis(self, submissions: List[Dict[str, any]]) -> List[FinalPlagiarismReport]:
        """
        Runs the full analysis on a batch of submissions.
        1. Normalization
        2. Shortlisting
        3. Detailed Comparison
        4. Aggregation
        """
        print(f"Starting batch analysis for {len(submissions)} submissions...")
        
        # 1. Normalize all submissions
        normalized_data = []
        for sub in submissions:
            norm_result = await self.norm_service.normalize_submission(sub["id"], sub["files"])
            normalized_data.append(norm_result)

        # 2. Shortlist suspicious pairs
        print("Shortlisting suspicious candidates...")
        # Prepare data for shortlisting service
        shortlist_input = []
        for n in normalized_data:
            shortlist_input.append({
                "id": n.submission_id,
                "files": {f.original_path: f.normalized_content for f in n.files},
                "language": n.files[0].language if n.files else "unknown"
            })

        report = await self.shortlisting_service.shortlist(
            challenge_id="local_repo", 
            submissions=shortlist_input
        )
        
        final_reports = []
        
        # 3. Analyze each shortlisted pair
        print(f"Found {len(report.shortlisted_pairs)} suspicious pairs. Running deep analysis...")
        for pair in report.shortlisted_pairs:
            # Find the normalized results for A and B
            norm_a = next(n for n in normalized_data if n.submission_id == pair.submission_id_a)
            norm_b = next(n for n in normalized_data if n.submission_id == pair.submission_id_b)
            
            # For simplicity, we compare the first files (usually the main file in a hackathon)
            content_a = norm_a.files[0].normalized_content
            content_b = norm_b.files[0].normalized_content
            raw_a = norm_a.files[0].raw_content
            raw_b = norm_b.files[0].raw_content

            # A. Token Similarity
            fprints_a = self.fprinter.get_fingerprints(content_a)
            fprints_b = self.fprinter.get_fingerprints(content_b)
            token_score = round(self.fprinter.calculate_jaccard_similarity(fprints_a, fprints_b) * 100, 2)
            
            # B. AST Similarity
            ast_a = await self.ast_service.analyze_submission({norm_a.files[0].original_path: raw_a})
            ast_b = await self.ast_service.analyze_submission({norm_b.files[0].original_path: raw_b})
            ast_results = await self.ast_service.compare_submissions(ast_a, ast_b)
            ast_score = ast_results[0].structural_score if ast_results else 0.0
            
            # C. Aggregation
            final_report = await self.aggregator.aggregate(
                token_score=token_score,
                ast_score=ast_score,
                skeleton_score=pair.skeleton_similarity_score,
                embedding_score=0.0, # Placeholder
                gemini_score=0.0,    # Placeholder
                ai_likelihood=0.0,   # Placeholder
                meta_data={"id_a": pair.submission_id_a, "id_b": pair.submission_id_b}
            )
            final_reports.append(final_report)
            
        return final_reports
