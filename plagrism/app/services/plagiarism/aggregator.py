from typing import Dict, List, Optional
from app.schemas.final_report import FinalPlagiarismReport, AggregatorConfig

class ScoringAggregator:
    """
    Aggregates similarity scores from multiple detection layers into a final report.
    """

    def __init__(self, config: Optional[AggregatorConfig] = None):
        self.config = config or AggregatorConfig()

    async def aggregate(self,
                  token_score: float,
                  ast_score: float,
                  skeleton_score: float,
                  embedding_score: float,
                  gemini_score: float,
                  ai_likelihood: float,
                  meta_data: Dict[str, any] = {}) -> FinalPlagiarismReport:
        """
        Calculates the final peer plagiarism score using a weighted average.
        """
        
        # 1. Calculate Weighted Peer Plagiarism Score
        # We combine Token, AST, Skeleton, Embedding, and Gemini scores
        component_scores = {
            "token": token_score,
            "ast": ast_score,
            "skeleton": skeleton_score,
            "embedding": embedding_score,
            "gemini": gemini_score
        }
        
        total_weight = (self.config.token_weight + 
                        self.config.ast_weight + 
                        self.config.skeleton_weight + 
                        self.config.embedding_weight + 
                        self.config.gemini_weight)
        
        weighted_sum = (
            token_score * self.config.token_weight +
            ast_score * self.config.ast_weight +
            skeleton_score * self.config.skeleton_weight +
            embedding_score * self.config.embedding_weight +
            gemini_score * self.config.gemini_weight
        )
        
        final_peer_score = round(weighted_sum / total_weight, 2)
        
        # 2. Determine Risk Level
        risk_level = self._determine_risk_level(final_peer_score)
        
        # 3. Compile Evidence Highlights
        highlights = []
        if token_score > 70: highlights.append("Near-identical token fingerprint match found.")
        if ast_score > 80: highlights.append("Deep structural/AST similarity detected.")
        if gemini_score > 60: highlights.append("AI Semantic Review flagged suspicious logical overlaps.")
        if ai_likelihood > 70: highlights.append("Stylometric signals suggest potential AI generation.")

        return FinalPlagiarismReport(
            submission_id_a=meta_data.get("id_a", "unknown"),
            submission_id_b=meta_data.get("id_b", "unknown"),
            peer_plagiarism_percentage=final_peer_score,
            ai_baseline_similarity_percentage=embedding_score, # Using embeddings as a baseline for AI-like conceptual overlap
            ai_likelihood_percentage=ai_likelihood,
            final_review_risk=risk_level,
            review_reason_summary=self._generate_summary(final_peer_score, risk_level, highlights),
            evidence_highlights=highlights,
            component_scores=component_scores
        )

    def _determine_risk_level(self, score: float) -> str:
        if score >= 75: return "high"
        if score >= 45: return "medium"
        if score >= 20: return "low"
        return "minimal"

    def _generate_summary(self, score: float, risk: str, highlights: List[str]) -> str:
        if risk == "high":
            return f"CRITICAL: High risk match ({score}%). Multiple layers confirmed identical logic and structure."
        if risk == "medium":
            return f"WARNING: Suspicious match ({score}%). Found significant structural or semantic overlap."
        if risk == "low":
            return f"Low risk ({score}%). Some common patterns found, likely boilerplate or shared library usage."
        return "Minimal similarity detected."
